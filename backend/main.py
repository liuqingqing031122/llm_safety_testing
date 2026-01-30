from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime
import time
from . import auth  # Import auth router
from .auth import get_current_user_optional
from .models import Base, User

from .models.database import init_db, get_db, Conversation, ConversationTurn, ModelResponse, engine

from dotenv import load_dotenv
load_dotenv()
from .models.llm_client import LLMClient
from .models.prompt_detector import PromptTypeDetector
from .models.references_routes import router as reference_router, set_reference_loader
from .models.reference_loader import ReferenceLoader

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize
init_db()
llm_client = LLMClient()
prompt_detector = PromptTypeDetector()
reference_loader = ReferenceLoader()

set_reference_loader(reference_loader)
app.include_router(reference_router)
app.include_router(auth.router)

# Pydantic models
class ConversationCreate(BaseModel):
    models: List[str]

class SendMessageRequest(BaseModel):
    message: str
    models: List[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/api/conversations")
async def create_conversation(
    request: ConversationCreate, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)  # ✅ Make optional
):
    """Create a new conversation"""
    conversation = Conversation(
        user_id=current_user.id if current_user else None  # ✅ None if not logged in
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return {
        "conversation_id": conversation.id,
        "created_at": conversation.created_at.isoformat(),
        "models": request.models,
        "user_id": conversation.user_id
    }


@app.post("/api/conversations/{conversation_id}/send")
async def send_message(
    conversation_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db)
):
    """
    ✅ OPTIMIZED: Send a message and get responses from ALL models in PARALLEL
    
    Speed improvement: 
    - Before: Sequential (80 min for 4 models × 5 runs)
    - After: Parallel (10 min max - limited by slowest model)
    """
    
    # Get conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get turn number
    turn_number = db.query(ConversationTurn).filter(
        ConversationTurn.conversation_id == conversation_id
    ).count() + 1
    
    # Detect prompt type
    detection_result = prompt_detector.detect_prompt_type(
        message=request.message,
        turn_number=turn_number
    )
    
    prompt_type = detection_result["type"]
    runs_per_model = detection_result["runs_per_model"]
    
    print(f"🎯 Detected prompt type: {prompt_type}")
    print(f"🔄 Will run {runs_per_model} times per model")
    print(f"💡 Reasoning: {detection_result.get('reasoning', 'N/A')}")
    
    # Update conversation
    conversation.prompt_type = prompt_type
    conversation.runs_per_model = runs_per_model
    db.commit()
    
    # Create conversation turn
    turn = ConversationTurn(
        conversation_id=conversation_id,
        turn_number=turn_number,
        user_message=request.message
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    
    # Get conversation history for context (if needed)
    conversation_history = []
    if turn_number > 1:
        previous_turns = db.query(ConversationTurn).filter(
            ConversationTurn.conversation_id == conversation_id,
            ConversationTurn.turn_number < turn_number
        ).order_by(ConversationTurn.turn_number).all()
        
        for prev_turn in previous_turns:
            for model_name in request.models:
                prev_response = db.query(ModelResponse).filter(
                    ModelResponse.conversation_turn_id == prev_turn.id,
                    ModelResponse.model_name == model_name
                ).first()
                if prev_response:
                    conversation_history.append({
                        "role": "user",
                        "content": prev_turn.user_message
                    })
                    conversation_history.append({
                        "role": "assistant",
                        "content": prev_response.response_text
                    })
                    break
    
    # ✅ PARALLEL EXECUTION: Create all tasks upfront
    print(f"\n🚀 Generating {len(request.models)} models × {runs_per_model} runs in PARALLEL...")
    
    tasks = []
    task_metadata = []  # Track which task is for which model/run
    
    for model_name in request.models:
        for run in range(runs_per_model):
            # Create async task
            task = llm_client.generate_response(
                model_name=model_name,
                message=request.message,
                conversation_history=conversation_history
            )
            tasks.append(task)
            task_metadata.append({
                "model_name": model_name,
                "run": run + 1,
                "start_time": time.time()
            })
    
    # ✅ Execute ALL tasks simultaneously
    print(f"⚡ Running {len(tasks)} API calls simultaneously...")
    overall_start = time.time()
    
    # Gather all responses (handles exceptions gracefully)
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - overall_start
    print(f"✅ All {len(tasks)} calls completed in {total_time:.2f}s!")
    
    # Save all responses to database
    all_responses = []
    
    for i, response_text in enumerate(responses):
        metadata = task_metadata[i]
        model_name = metadata["model_name"]
        run_number = metadata["run"]
        response_time = time.time() - metadata["start_time"]
        
        # Handle exceptions
        if isinstance(response_text, Exception):
            print(f"❌ Error for {model_name} run {run_number}: {response_text}")
            response_text = f"Error: {str(response_text)}"
        
        try:
            # Save response
            model_response = ModelResponse(
                conversation_turn_id=turn.id,
                model_name=model_name,
                response_text=response_text,
                response_time=response_time,
                scored=False,
                score_data=None,
                weighted_score=None
            )
            db.add(model_response)
            db.commit()
            db.refresh(model_response)
            
            all_responses.append({
                "id": model_response.id,
                "model_name": model_name,
                "response_text": response_text,
                "response_time": response_time,
                "run_number": run_number,
                "scored": False
            })
            
            print(f"   ✅ {model_name} run {run_number}: {response_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Error saving response for {model_name} run {run_number}: {e}")
            continue
    
    return {
        "turn_id": turn.id,
        "turn_number": turn_number,
        "prompt_type": prompt_type,
        "runs_per_model": runs_per_model,
        "detection_info": detection_result,
        "responses": all_responses,
        "total_time": total_time  # ✨ Show total execution time
    }


@app.post("/api/conversations/{conversation_id}/score")
async def start_scoring(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    ✅ OPTIMIZED: Score all responses in PARALLEL
    
    Speed improvement:
    - Before: Sequential (5 min for 20 responses)
    - After: Parallel (30 sec for 20 responses)
    """
    from .models.scoring import MedicalResponseScorer
    
    # Check conversation exists
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get unscored responses
    unscored_responses = db.query(ModelResponse).join(ConversationTurn).filter(
        ConversationTurn.conversation_id == conversation_id,
        ModelResponse.scored == False
    ).all()
    
    if not unscored_responses:
        return {
            "status": "complete",
            "message": "All responses already scored",
            "scored_count": 0,
            "total_responses": 0
        }
    
    print(f"📊 Starting PARALLEL scoring for {len(unscored_responses)} responses...")
    
    # Initialize scorer
    scorer = MedicalResponseScorer()
    
    # ✅ Create scoring tasks in parallel
    async def score_response(response):
        """Score a single response"""
        try:
            turn = db.query(ConversationTurn).filter(
                ConversationTurn.id == response.conversation_turn_id
            ).first()
            
            # Get conversation history (for conversational prompts)
            conversation_history = []
            if turn.turn_number > 1:
                previous_turns = db.query(ConversationTurn).filter(
                    ConversationTurn.conversation_id == conversation_id,
                    ConversationTurn.turn_number < turn.turn_number
                ).order_by(ConversationTurn.turn_number).all()
                
                for prev_turn in previous_turns:
                    prev_response = db.query(ModelResponse).filter(
                        ModelResponse.conversation_turn_id == prev_turn.id,
                        ModelResponse.model_name == response.model_name
                    ).first()
                    
                    if prev_response:
                        conversation_history.append((
                            prev_turn.user_message,
                            prev_response.response_text
                        ))
            
            # Score the response
            print(f"   Scoring response {response.id} ({response.model_name})...")
            
            score_result = await scorer.score_response_async(
                question=turn.user_message,
                response=response.response_text,
                prompt_type=conversation.prompt_type,
                turn_number=turn.turn_number,
                conversation_history=conversation_history
            )
            
            # Update response
            response.scored = True
            response.score_data = score_result
            response.weighted_score = score_result.get('weighted_score', 0)
            
            print(f"   ✅ Response {response.id}: Score {response.weighted_score}/100")
            
            return {"success": True, "response_id": response.id}
            
        except Exception as e:
            print(f"❌ Error scoring response {response.id}: {e}")
            return {"success": False, "response_id": response.id, "error": str(e)}
    
    # ✅ Run all scoring tasks in parallel
    start_time = time.time()
    
    scoring_tasks = [score_response(r) for r in unscored_responses]
    results = await asyncio.gather(*scoring_tasks, return_exceptions=True)
    
    # Commit all changes at once
    db.commit()
    
    total_time = time.time() - start_time
    
    # Count successes
    scored_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    errors = [r for r in results if isinstance(r, dict) and not r.get("success")]
    
    print(f"✅ Scored {scored_count}/{len(unscored_responses)} responses in {total_time:.2f}s")
    
    return {
        "status": "complete",
        "conversation_id": conversation_id,
        "scored_count": scored_count,
        "total_responses": len(unscored_responses),
        "total_time": total_time,
        "errors": errors if errors else None
    }


@app.get("/api/conversations/{conversation_id}/scores")
async def get_scores(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    获取 conversation 的所有评分结果
    """
    # Get all scored responses
    scored_responses = db.query(ModelResponse).join(ConversationTurn).filter(
        ConversationTurn.conversation_id == conversation_id,
        ModelResponse.scored == True
    ).all()
    
    if not scored_responses:
        return {
            "conversation_id": conversation_id,
            "message": "No scored responses yet",
            "results": []
        }
    
    # Group by model
    results_by_model = {}
    
    for response in scored_responses:
        model = response.model_name
        if model not in results_by_model:
            results_by_model[model] = {
                "model_name": model,
                "total_responses": 0,
                "scored_responses": 0,
                "average_score": 0,
                "min_score": None,
                "max_score": None,
                "scores": []
            }
        
        results_by_model[model]["total_responses"] += 1
        
        if response.weighted_score is not None:
            results_by_model[model]["scored_responses"] += 1
            results_by_model[model]["scores"].append(response.weighted_score)
    
    # Calculate statistics
    for model in results_by_model:
        scores = results_by_model[model]["scores"]
        if scores:
            results_by_model[model]["average_score"] = round(sum(scores) / len(scores), 2)
            results_by_model[model]["min_score"] = round(min(scores), 2)
            results_by_model[model]["max_score"] = round(max(scores), 2)
    
    return {
        "conversation_id": conversation_id,
        "results": list(results_by_model.values())
    }


@app.get("/api/responses/{response_id}/score-detail")
async def get_score_detail(
    response_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个 response 的详细评分信息
    """
    response = db.query(ModelResponse).filter(
        ModelResponse.id == response_id
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    if not response.scored:
        return {
            "response_id": response_id,
            "scored": False,
            "message": "Response not yet scored"
        }
    
    return {
        "response_id": response_id,
        "model_name": response.model_name,
        "scored": True,
        "weighted_score": response.weighted_score,
        "score_data": response.score_data,
        "response_text": response.response_text[:300] + "..." if len(response.response_text) > 300 else response.response_text
    }


@app.get("/api/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get full conversation history"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    turns = db.query(ConversationTurn).filter(
        ConversationTurn.conversation_id == conversation_id
    ).order_by(ConversationTurn.turn_number).all()
    
    history = []
    for turn in turns:
        responses = db.query(ModelResponse).filter(
            ModelResponse.conversation_turn_id == turn.id
        ).all()
        
        history.append({
            "turn_number": turn.turn_number,
            "user_message": turn.user_message,
            "timestamp": turn.timestamp.isoformat(),
            "model_responses": [
                {
                    "id": r.id,
                    "model_name": r.model_name,
                    "response_text": r.response_text,
                    "response_time": r.response_time,
                    "scored": r.scored,
                    "weighted_score": r.weighted_score,
                    "score_data": r.score_data
                }
                for r in responses
            ]
        })
    
    return {
        "conversation_id": conversation_id,
        "prompt_type": conversation.prompt_type,
        "runs_per_model": conversation.runs_per_model,
        "created_at": conversation.created_at.isoformat(),
        "turns": history
    }

@app.get("/api/conversations/{conversation_id}/final-summary")
async def get_final_summary(conversation_id: int, db: Session = Depends(get_db)):
    """
    Calculate and return average scores per model + recommendations + category breakdowns
    """

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Get all responses for this conversation
    responses = db.query(ModelResponse).join(ConversationTurn).filter(
        ConversationTurn.conversation_id == conversation_id,
        ModelResponse.scored == True
    ).all()

    if not responses:
        return {"error": "No scored responses"}

    # Group by model - collect both overall scores and category scores
    model_scores = {}
    model_category_scores = {}
    
    for resp in responses:
        model = resp.model_name
        
        # Initialize if needed
        if model not in model_scores:
            model_scores[model] = []
            model_category_scores[model] = {}
        
        # Add overall score
        if resp.weighted_score is not None:
            model_scores[model].append(resp.weighted_score)
        
        # Extract category scores from score_data
        if resp.score_data and 'raw_scores' in resp.score_data:
            raw_scores = resp.score_data['raw_scores']
            
            # Collect each category score (excluding 'reasoning')
            for category, score in raw_scores.items():
                if category != 'reasoning' and isinstance(score, (int, float)):
                    if category not in model_category_scores[model]:
                        model_category_scores[model][category] = []
                    model_category_scores[model][category].append(score)

    # Compute overall averages
    averages = {
        model: round(sum(scores) / len(scores), 2)
        for model, scores in model_scores.items()
    }
    
    # Compute category averages across all runs
    category_averages = {}
    for model, categories in model_category_scores.items():
        category_averages[model] = {}
        for category, scores in categories.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                category_averages[model][category] = round(avg_score, 3)
                print(f"   📊 {model} - {category}: {scores} → avg: {avg_score:.3f}")

    # Determine recommendation
    if len(averages) == 1:
        recommended = list(averages.keys())
        max_score = list(averages.values())[0]
    else:
        max_score = max(averages.values())
        recommended = [m for m, avg in averages.items() if avg == max_score]

    return {
        "conversation_id": conversation_id,
        "averages": averages,
        "category_averages": category_averages,
        "recommended_models": recommended,
        "max_score": max_score,
        "prompt_type": conversation.prompt_type
    }

@app.get("/")
def read_root():
    return {"message": "Medical LLM Safety Benchmark API"}

# Add this new endpoint in backend/main.py

@app.get("/api/users/conversations")
async def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user_dependency)
):
    """Get all conversations for the current user"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()
    
    result = []
    for conv in conversations:
        # Get first turn to show preview
        first_turn = db.query(ConversationTurn).filter(
            ConversationTurn.conversation_id == conv.id
        ).order_by(ConversationTurn.turn_number).first()
        
        # Count total turns
        turn_count = db.query(ConversationTurn).filter(
            ConversationTurn.conversation_id == conv.id
        ).count()
        
        result.append({
            "id": conv.id,
            "created_at": conv.created_at.isoformat(),
            "prompt_type": conv.prompt_type,
            "runs_per_model": conv.runs_per_model,
            "preview": first_turn.user_message if first_turn else "No messages",
            "turn_count": turn_count
        })
    
    return {
        "conversations": result,
        "total": len(result)
    }

@app.get("/api/conversations/{conversation_id}/full-details")
async def get_conversation_full_details(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user_dependency)
):
    """Get full conversation details including history and summary"""
    
    # Verify this conversation belongs to the user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get conversation history
    turns = db.query(ConversationTurn).filter(
        ConversationTurn.conversation_id == conversation_id
    ).order_by(ConversationTurn.turn_number).all()
    
    history = []
    for turn in turns:
        responses = db.query(ModelResponse).filter(
            ModelResponse.conversation_turn_id == turn.id
        ).all()
        
        history.append({
            "turn_number": turn.turn_number,
            "user_message": turn.user_message,
            "timestamp": turn.timestamp.isoformat(),
            "model_responses": [
                {
                    "id": r.id,
                    "model_name": r.model_name,
                    "response_text": r.response_text,
                    "response_time": r.response_time,
                    "scored": r.scored,
                    "weighted_score": r.weighted_score,
                    "score_data": r.score_data
                }
                for r in responses
            ]
        })
    
    # Get final summary if scored
    final_summary = None
    if any(r.scored for turn in turns for r in 
           db.query(ModelResponse).filter(ModelResponse.conversation_turn_id == turn.id).all()):
        
        # Calculate summary (same logic as /final-summary endpoint)
        responses = db.query(ModelResponse).join(ConversationTurn).filter(
            ConversationTurn.conversation_id == conversation_id,
            ModelResponse.scored == True
        ).all()
        
        if responses:
            model_scores = {}
            for resp in responses:
                model = resp.model_name
                if model not in model_scores:
                    model_scores[model] = []
                if resp.weighted_score is not None:
                    model_scores[model].append(resp.weighted_score)
            
            averages = {
                model: round(sum(scores) / len(scores), 2)
                for model, scores in model_scores.items()
            }
            
            if averages:
                max_score = max(averages.values())
                recommended = [m for m, avg in averages.items() if avg == max_score]
                
                final_summary = {
                    "averages": averages,
                    "recommended_models": recommended,
                    "max_score": max_score
                }
    
    return {
        "conversation_id": conversation_id,
        "prompt_type": conversation.prompt_type,
        "runs_per_model": conversation.runs_per_model,
        "created_at": conversation.created_at.isoformat(),
        "turns": history,
        "final_summary": final_summary
    }

if __name__ == "__main__":
    import uvicorn
    import os
    print("🚀 Starting Medical LLM Benchmark API...")
    port = int(os.environ.get("PORT", 8000))
    print(f"📍 API docs: http://0.0.0.0:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)