from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime

from models.database import init_db, get_db, Conversation, ConversationTurn, ModelResponse

from dotenv import load_dotenv
load_dotenv()
from models.llm_client import LLMClient
from models.prompt_detector import PromptTypeDetector

app = FastAPI()

# CORS
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
async def create_conversation(request: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation"""
    conversation = Conversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return {
        "conversation_id": conversation.id,
        "created_at": conversation.created_at.isoformat(),
        "models": request.models
    }


@app.post("/api/conversations/{conversation_id}/send")
async def send_message(
    conversation_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db)
):
    """Send a message and get responses from selected models"""
    
    # Get conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get turn number
    turn_number = db.query(ConversationTurn).filter(
        ConversationTurn.conversation_id == conversation_id
    ).count() + 1
    
    # ✨ 自动检测 prompt type 和运行次数
    detection_result = prompt_detector.detect_prompt_type(
        message=request.message,
        turn_number=turn_number
    )
    
    prompt_type = detection_result["type"]
    runs_per_model = detection_result["runs_per_model"]  # ✨ 使用检测器返回的值
    
    print(f"🎯 Detected prompt type: {prompt_type}")
    print(f"🔄 Will run {runs_per_model} times per model")
    print(f"💡 Reasoning: {detection_result.get('reasoning', 'N/A')}")
    
    # Update conversation
    conversation.prompt_type = prompt_type
    conversation.runs_per_model = runs_per_model  # ✨ 保存到数据库
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
    
    # Generate responses
    all_responses = []
    
    for model_name in request.models:
        print(f"\n🤖 Generating responses for {model_name}...")
        
        # ✨ 运行指定次数
        for run in range(runs_per_model):
            print(f"   Run {run + 1}/{runs_per_model}...")
            
            try:
                import time
                start_time = time.time()
                
                # Generate response with conversation history
                response_text = await llm_client.generate_response(
                    model_name=model_name,
                    message=request.message,
                    conversation_history=conversation_history
                )
                
                response_time = time.time() - start_time
                
                # Save response
                model_response = ModelResponse(
                    conversation_turn_id=turn.id,
                    model_name=model_name,
                    response_text=response_text,
                    response_time=response_time,
                    scored=False,  # ✨ 初始未评分
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
                    "run_number": run + 1,
                    "scored": False
                })
                
            except Exception as e:
                print(f"❌ Error generating response for {model_name} (run {run + 1}): {e}")
                continue
    
    return {
        "turn_id": turn.id,
        "turn_number": turn_number,
        "prompt_type": prompt_type,
        "runs_per_model": runs_per_model,
        "detection_info": detection_result,
        "responses": all_responses
    }


# ✨ 添加：开始评分
@app.post("/api/conversations/{conversation_id}/score")
async def start_scoring(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    开始对 conversation 的所有 responses 进行评分
    """
    from models.scoring import MedicalResponseScorer
    
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
    
    print(f"📊 Starting scoring for {len(unscored_responses)} responses...")
    
    # Initialize scorer
    scorer = MedicalResponseScorer()
    
    scored_count = 0
    errors = []
    
    for response in unscored_responses:
        try:
            turn = response.turn
            
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
            
            score_result = scorer.score_response(
                question=turn.user_message,
                response=response.response_text,
                prompt_type=conversation.prompt_type,
                turn_number=turn.turn_number,
                conversation_history=conversation_history
            )
            
            # Save score
            response.scored = True
            response.score_data = score_result
            response.weighted_score = score_result.get('weighted_score', 0)
            
            db.commit()
            scored_count += 1
            
            print(f"   ✅ Score: {response.weighted_score}/100")
            
        except Exception as e:
            print(f"   ❌ Error scoring response {response.id}: {e}")
            errors.append({
                "response_id": response.id,
                "model_name": response.model_name,
                "error": str(e)
            })
            continue
    
    return {
        "status": "complete",
        "conversation_id": conversation_id,
        "scored_count": scored_count,
        "total_responses": len(unscored_responses),
        "errors": errors if errors else None
    }


# ✨ 添加：获取评分结果
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


# ✨ 添加：获取详细评分
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
    Calculate and return average scores per model + recommendations
    """
    # Get all responses for this conversation
    responses = db.query(ModelResponse).join(ConversationTurn).filter(
        ConversationTurn.conversation_id == conversation_id,
        ModelResponse.scored == True
    ).all()

    if not responses:
        return {"error": "No scored responses"}

    # Group by model
    model_scores = {}
    for resp in responses:
        model = resp.model_name
        model_scores.setdefault(model, [])
        if resp.weighted_score is not None:
            model_scores[model].append(resp.weighted_score)

    # Compute averages
    averages = {
        model: round(sum(scores) / len(scores), 2)
        for model, scores in model_scores.items()
    }

    # Determine recommendation
    if len(averages) == 1:
        recommended = list(averages.keys())
    else:
        max_score = max(averages.values())
        recommended = [m for m, avg in averages.items() if avg == max_score]

    return {
        "conversation_id": conversation_id,
        "averages": averages,
        "recommended_models": recommended,
        "max_score": max_score,
    }



if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Medical LLM Benchmark API...")
    print("📍 API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)