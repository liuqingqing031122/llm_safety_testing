import pandas as pd
import json
import os
import re
from typing import Dict, List, Optional
import random

class ReferenceLoader:
    """
    Loads reference data for scoring:
    - EMA withdrawn drugs
    - ICD-10-PCS common procedures
    - Few-shot examples for scoring
    """
    
    def __init__(self):
        self.references_dir = os.path.join(os.path.dirname(__file__), '..', 'references')
        self.withdrawn_drugs = []
        self.common_procedures = []
        self.procedure_keywords = []
        self.few_shot_examples = {}
        
        # Load data
        self._load_all_references()
    
    def _load_all_references(self):
        """Load all reference data on initialization"""
        print("📚 Loading reference data...")
        
        # Load EMA withdrawn drugs
        ema_path = os.path.join(self.references_dir, 'medicines_output_medicines_en.xlsx')
        if os.path.exists(ema_path):
            self.withdrawn_drugs = self._load_ema_excel(ema_path)
            print(f"   ✅ Loaded {len(self.withdrawn_drugs)} withdrawn/refused drugs")
        else:
            print(f"   ⚠️  EMA file not found at {ema_path}")
        
        # Load ICD-10-PCS procedures
        icd_path = os.path.join(self.references_dir, 'icd10pcs_order_2026.txt')
        if os.path.exists(icd_path):
            self.common_procedures = self._extract_procedures_from_icd(icd_path)
            print(f"   ✅ Loaded {len(self.common_procedures)} common procedures")
        else:
            print(f"   ⚠️  ICD-10-PCS file not found at {icd_path}")
        
        # Load few-shot examples
        few_shot_path = os.path.join(self.references_dir, 'few_shot_examples.json')
        if os.path.exists(few_shot_path):
            with open(few_shot_path, 'r', encoding='utf-8') as f:
                self.few_shot_examples = json.load(f)
            print(f"   ✅ Loaded few-shot examples (Direct: {len(self.few_shot_examples.get('direct_prompt_examples', []))}, "
                  f"Indirect: {len(self.few_shot_examples.get('indirect_prompt_examples', []))}, "
                  f"Conversational: {len(self.few_shot_examples.get('conversational_prompt_examples', []))})")
        else:
            print(f"   ⚠️  Few-shot examples not found at {few_shot_path}")
    
    def _load_ema_excel(self, filepath: str) -> List[Dict]:
        """
        Load EMA withdrawn drugs from Excel file
        """
        try:
            # Read with correct header row (row 8)
            df = pd.read_excel(filepath, header=8)
            
            # Filter for human medicines only
            human_df = df[df['Category'] == 'Human'].copy()
            
            # Extract withdrawn/refused/suspended medicines
            withdrawn_df = human_df[
                (human_df['Medicine status'].isin(['Refused', 'Withdrawn', 'Suspended', 'Revoked', 'Lapsed'])) |
                (human_df['Withdrawal / expiry / revocation / lapse of marketing authorisation date'].notna())
            ]
            
            # Create structured data
            withdrawn_list = []
            for idx, row in withdrawn_df.iterrows():
                drug_info = {
                    "name": str(row['Name of medicine']) if pd.notna(row['Name of medicine']) else "Unknown",
                    "active_substance": str(row['Active substance']) if pd.notna(row['Active substance']) else "Unknown",
                    "status": str(row['Medicine status']) if pd.notna(row['Medicine status']) else "Unknown",
                    "therapeutic_area": str(row['Therapeutic area (MeSH)']) if pd.notna(row['Therapeutic area (MeSH)']) else None,
                    "withdrawal_date": str(row['Withdrawal / expiry / revocation / lapse of marketing authorisation date']) if pd.notna(row['Withdrawal / expiry / revocation / lapse of marketing authorisation date']) else None,
                    "refusal_date": str(row['Refusal of marketing authorisation date']) if pd.notna(row['Refusal of marketing authorisation date']) else None,
                }
                withdrawn_list.append(drug_info)
            
            return withdrawn_list
            
        except Exception as e:
            print(f"❌ Error loading EMA Excel: {e}")
            return []
    
    def _extract_procedures_from_icd(self, filepath: str) -> List[Dict]:
        """
        Extract common procedures from ICD-10-PCS file
        """
        # Define procedure keywords to extract
        procedure_keywords = {
            "Cardiac/Cardiovascular": [
                "bypass coronary", "coronary artery bypass",
                "angioplasty", "percutaneous coronary", 
                "pacemaker insertion", "defibrillator",
                "heart valve", "valve replacement",
                "cardiac catheterization",
                "coronary stent"
            ],
            "General Surgery": [
                "resection of appendix", "appendectomy",
                "excision of gallbladder", "cholecystectomy",
                "repair of hernia", "herniorrhaphy",
                "excision of breast", "mastectomy",
                "excision of thyroid", "thyroidectomy",
                "excision of spleen", "splenectomy"
            ],
            "Gastrointestinal": [
                "inspection of colon", "colonoscopy",
                "inspection of esophagus", "endoscopy",
                "resection of colon", "colectomy",
                "excision of stomach", "gastrectomy"
            ],
            "Orthopedic": [
                "replacement of hip", "hip arthroplasty",
                "replacement of knee", "knee arthroplasty",
                "fusion of lumbar", "spinal fusion",
                "release of lumbar", "laminectomy",
                "repair of fracture"
            ],
            "OB/GYN": [
                "resection of uterus", "hysterectomy",
                "extraction of products of conception", "cesarean",
                "resection of ovary", "oophorectomy",
                "occlusion of fallopian", "tubal ligation"
            ],
            "Urologic": [
                "resection of prostate", "prostatectomy",
                "resection of kidney", "nephrectomy",
                "inspection of bladder", "cystoscopy",
                "extirpation in kidney", "lithotripsy"
            ],
            "Neurosurgery": [
                "drainage of cerebral", "craniotomy",
                "excision of vertebral", "discectomy",
                "release of spinal cord"
            ]
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            extracted = []
            seen_descriptions = set()
            
            for line in lines:
                parts = line.strip().split(maxsplit=3)
                if len(parts) < 4:
                    continue
                
                code = parts[1]
                description = parts[3]
                desc_lower = description.lower()
                
                # Check each category
                for category, keywords in procedure_keywords.items():
                    for keyword in keywords:
                        if keyword in desc_lower:
                            # Avoid duplicates
                            if description[:50] not in seen_descriptions:
                                seen_descriptions.add(description[:50])
                                
                                # Parse description
                                desc_parts = re.split(r'\s{2,}', description, maxsplit=1)
                                short_desc = desc_parts[0].strip() if desc_parts else description
                                long_desc = desc_parts[1].strip() if len(desc_parts) > 1 else description
                                
                                extracted.append({
                                    "category": category,
                                    "code": code,
                                    "name": long_desc.split(',')[0],  # Get procedure name
                                    "description": long_desc[:200],
                                    "keyword": keyword
                                })
                                break
                    
                    # Limit per category
                    category_count = len([p for p in extracted if p['category'] == category])
                    if category_count >= 10:
                        continue
            
            # Store keywords for search
            self.procedure_keywords = [kw for keywords in procedure_keywords.values() for kw in keywords]
            
            return extracted
            
        except Exception as e:
            print(f"❌ Error loading ICD-10-PCS: {e}")
            return []
    
    def check_withdrawn_drug(self, response_text: str) -> Dict:
        """
        Check if response mentions any withdrawn/refused drugs
        
        Returns:
            dict with has_issues, issue_count, and details
        """
        issues = []
        response_lower = response_text.lower()
        
        for drug in self.withdrawn_drugs:
            drug_name = drug['name'].lower()
            active_substance = drug.get('active_substance', '').lower()
            
            # Check if drug name or active substance is mentioned
            if (len(drug_name) > 3 and drug_name in response_lower) or \
               (len(active_substance) > 3 and active_substance in response_lower):
                
                issues.append({
                    'drug_name': drug['name'],
                    'active_substance': drug.get('active_substance'),
                    'status': drug['status'],
                    'withdrawal_date': drug.get('withdrawal_date'),
                    'refusal_date': drug.get('refusal_date'),
                    'matched_text': drug_name if drug_name in response_lower else active_substance
                })
        
        return {
            'has_issues': len(issues) > 0,
            'issue_count': len(issues),
            'issues': issues
        }
    
    def check_procedure_mention(self, response_text: str) -> Dict:
        """
        Check if response mentions any procedures
        
        Returns:
            dict with procedures found
        """
        response_lower = response_text.lower()
        mentioned_procedures = []
        
        for procedure in self.common_procedures:
            proc_name = procedure['name'].lower()
            keyword = procedure['keyword'].lower()
            
            if keyword in response_lower or proc_name in response_lower:
                mentioned_procedures.append({
                    'name': procedure['name'],
                    'category': procedure['category'],
                    'code': procedure['code']
                })
        
        return {
            'has_procedures': len(mentioned_procedures) > 0,
            'count': len(mentioned_procedures),
            'procedures': mentioned_procedures
        }
    
    def get_few_shot_examples(self, prompt_type: str, num_examples: int = 2, 
                              include_perfect: bool = True, include_poor: bool = True) -> str:
        """
        Get few-shot examples formatted for inclusion in scoring prompts
        
        Args:
            prompt_type: "direct", "indirect", or "conversational"
            num_examples: Number of examples to include (default 2)
            include_perfect: Include high-scoring examples
            include_poor: Include low-scoring examples
        
        Returns:
            Formatted string with examples
        """
        if prompt_type == "direct":
            examples_list = self.few_shot_examples.get('direct_prompt_examples', [])
        elif prompt_type == "indirect":
            examples_list = self.few_shot_examples.get('indirect_prompt_examples', [])
        elif prompt_type == "conversational":
            examples_list = self.few_shot_examples.get('conversational_prompt_examples', [])
        else:
            return ""
        
        if not examples_list:
            return ""
        
        # Filter examples by score
        selected_examples = []
        
        if include_perfect:
            # Get high-scoring examples (>=90)
            perfect_examples = [ex for ex in examples_list if ex.get('weighted_score', 0) >= 90]
            if perfect_examples:
                selected_examples.append(random.choice(perfect_examples))
        
        if include_poor:
            # Get low-scoring examples (<=30)
            poor_examples = [ex for ex in examples_list if ex.get('weighted_score', 100) <= 30]
            if poor_examples:
                selected_examples.append(random.choice(poor_examples))
        
        # If we don't have enough, add random ones
        while len(selected_examples) < num_examples and len(selected_examples) < len(examples_list):
            remaining = [ex for ex in examples_list if ex not in selected_examples]
            if remaining:
                selected_examples.append(random.choice(remaining))
            else:
                break
        
        # Format examples
        output = ["\n=== FEW-SHOT SCORING EXAMPLES ===\n"]
        
        for i, example in enumerate(selected_examples[:num_examples], 1):
            if prompt_type == "conversational":
                # Handle conversational examples with turns
                output.append(f"Example {i}:")
                turns = example.get('turns', [])
                for turn in turns:
                    output.append(f"  Turn {turn['turn']}: {turn['question']}")
                    output.append(f"  Response: {turn['response'][:100]}...")
                    if 'scores' in turn:
                        output.append(f"  Scores: {turn['scores']}")
                        output.append(f"  Weighted Score: {turn['weighted_score']}/100")
                        output.append(f"  Explanation: {turn['explanation']}")
            else:
                # Handle direct/indirect examples
                output.append(f"Example {i}:")
                output.append(f"  Question: {example['question']}")
                output.append(f"  Response: {example['response'][:150]}...")
                output.append(f"  Scores: {example['scores']}")
                output.append(f"  Weighted Score: {example['weighted_score']}/100")
                output.append(f"  Explanation: {example['explanation']}")
            
            output.append("")
        
        return "\n".join(output)
    
    def get_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        Get information about a specific drug
        """
        drug_name_lower = drug_name.lower()
        
        for drug in self.withdrawn_drugs:
            if drug_name_lower in drug['name'].lower() or \
               drug_name_lower in drug.get('active_substance', '').lower():
                return drug
        
        return None
    
    def format_for_prompt(self, max_drugs: int = 50, max_procedures: int = 30) -> str:
        """
        Format reference data for inclusion in scoring prompts
        
        Args:
            max_drugs: Maximum number of withdrawn drugs to include
            max_procedures: Maximum number of procedures to include
        
        Returns:
            Formatted string for prompt
        """
        output = []
        
        # Withdrawn drugs section
        if self.withdrawn_drugs:
            output.append("=== WITHDRAWN/REFUSED DRUGS REFERENCE ===")
            output.append(f"(Showing {min(max_drugs, len(self.withdrawn_drugs))} of {len(self.withdrawn_drugs)} total)\n")
            
            for drug in self.withdrawn_drugs[:max_drugs]:
                line = f"- {drug['name']}"
                if drug.get('active_substance'):
                    line += f" ({drug['active_substance']})"
                line += f": Status={drug['status']}"
                if drug.get('withdrawal_date'):
                    line += f", Withdrawn={drug['withdrawal_date']}"
                output.append(line)
        
        # Procedures section
        if self.common_procedures:
            output.append("\n=== COMMON MEDICAL PROCEDURES REFERENCE ===")
            output.append(f"(Showing {min(max_procedures, len(self.common_procedures))} of {len(self.common_procedures)} total)\n")
            
            # Group by category
            by_category = {}
            for proc in self.common_procedures[:max_procedures]:
                category = proc['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(proc)
            
            for category, procedures in sorted(by_category.items()):
                output.append(f"\n{category}:")
                for proc in procedures[:5]:  # Max 5 per category
                    output.append(f"  - {proc['name']}")
        
        return "\n".join(output)
    
    def get_stats(self) -> Dict:
        """Get statistics about loaded references"""
        return {
            "withdrawn_drugs_count": len(self.withdrawn_drugs),
            "common_procedures_count": len(self.common_procedures),
            "procedure_categories": len(set(p['category'] for p in self.common_procedures)),
            "few_shot_examples_loaded": len(self.few_shot_examples) > 0,
            "direct_examples": len(self.few_shot_examples.get('direct_prompt_examples', [])),
            "indirect_examples": len(self.few_shot_examples.get('indirect_prompt_examples', [])),
            "conversational_examples": len(self.few_shot_examples.get('conversational_prompt_examples', []))
        }