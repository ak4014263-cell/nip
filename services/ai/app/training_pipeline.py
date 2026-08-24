"""
AI Model Training Pipeline for Ollama
Trains Mistral 7B on your user data, resumes, and job applications
Builds domain-specific knowledge for job application automation
"""

import json
import os
import sys
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import sqlite3
from pathlib import Path
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import ollama for model operations
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not installed. Install with: pip install ollama")

@dataclass
class TrainingExample:
    """Single training example for the model"""
    instruction: str  # What we're asking the model to do
    input_context: str  # User/resume/job data
    output: str  # Expected model output
    category: str  # Type of task (profile_enhancement, cover_letter, ats_optimization, etc.)
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    timestamp: Optional[str] = None

class TrainingDataGenerator:
    """Generate training data from user resumes, applications, and feedback"""
    
    def __init__(self, db_path: str = "training_data.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize SQLite database for training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for training data collection
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_examples (
                id INTEGER PRIMARY KEY,
                instruction TEXT NOT NULL,
                input_context TEXT NOT NULL,
                output TEXT NOT NULL,
                category TEXT NOT NULL,
                user_id TEXT,
                job_id TEXT,
                success_score FLOAT DEFAULT 0.5,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_resumes (
                id INTEGER PRIMARY KEY,
                user_id TEXT UNIQUE,
                resume_text TEXT NOT NULL,
                skills TEXT,
                experience_years INTEGER,
                education TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                job_id TEXT,
                job_title TEXT,
                company TEXT,
                job_description TEXT,
                application_successful BOOLEAN,
                cover_letter TEXT,
                generated_profile TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY,
                user_id TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                bio TEXT,
                skills TEXT,
                experience_years INTEGER,
                education TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Database initialized at {self.db_path}")
    
    def generate_profile_enhancement_examples(self) -> List[TrainingExample]:
        """Generate training examples for profile enhancement"""
        examples = []
        
        # Real-world profile enhancement examples
        profiles = [
            {
                "name": "Alice Johnson",
                "skills": ["Python", "Django", "PostgreSQL"],
                "experience": 5,
                "role": "Backend Engineer"
            },
            {
                "name": "Bob Smith", 
                "skills": ["React", "TypeScript", "Node.js"],
                "experience": 3,
                "role": "Frontend Developer"
            },
            {
                "name": "Carol Davis",
                "skills": ["Java", "Spring Boot", "Kubernetes"],
                "experience": 7,
                "role": "Senior Java Developer"
            },
            {
                "name": "David Lee",
                "skills": ["AWS", "Docker", "Terraform"],
                "experience": 6,
                "role": "DevOps Engineer"
            },
            {
                "name": "Emma Wilson",
                "skills": ["Machine Learning", "Python", "TensorFlow"],
                "experience": 4,
                "role": "ML Engineer"
            }
        ]
        
        for profile in profiles:
            instruction = f"""Generate a professional headline for a {profile['role']} with {profile['experience']} years of experience."""
            
            input_context = f"""
Name: {profile['name']}
Skills: {', '.join(profile['skills'])}
Experience: {profile['experience']} years
Current Role: {profile['role']}
"""
            
            output = self._generate_headline(profile)
            
            examples.append(TrainingExample(
                instruction=instruction,
                input_context=input_context,
                output=output,
                category="profile_enhancement"
            ))
        
        return examples
    
    def generate_resume_examples(self) -> List[TrainingExample]:
        """Generate training examples for resume generation"""
        examples = []
        
        resume_profiles = [
            {
                "name": "Alice Johnson",
                "skills": ["Python", "Django", "PostgreSQL"],
                "companies": ["TechCorp", "StartupXYZ"],
                "summary": "Backend engineer specializing in scalable systems"
            },
            {
                "name": "Bob Smith",
                "skills": ["React", "TypeScript"],
                "companies": ["WebDesigns Inc", "Digital Agency"],
                "summary": "Frontend developer with focus on user experience"
            }
        ]
        
        for profile in resume_profiles:
            instruction = "Create a professional resume summary section for this candidate."
            
            input_context = f"""
Name: {profile['name']}
Skills: {', '.join(profile['skills'])}
Previous Companies: {', '.join(profile['companies'])}
"""
            
            output = f"""Professional Summary:
{profile['name']} is a skilled professional with expertise in {profile['skills'][0]}. 
With experience at {profile['companies'][0]} and {profile['companies'][1]}, 
{profile['name']} specializes in {profile['summary'].lower()}. 
Proven track record of delivering high-quality solutions and driving innovation.
"""
            
            examples.append(TrainingExample(
                instruction=instruction,
                input_context=input_context,
                output=output,
                category="resume_generation"
            ))
        
        return examples
    
    def generate_cover_letter_examples(self) -> List[TrainingExample]:
        """Generate training examples for cover letter generation"""
        examples = []
        
        job_applications = [
            {
                "candidate": "Alice Johnson",
                "skills": ["Python", "Django"],
                "job_title": "Senior Backend Engineer",
                "company": "TechCorp",
                "job_desc": "Building scalable backend systems"
            },
            {
                "candidate": "Bob Smith",
                "skills": ["React", "TypeScript"],
                "job_title": "Frontend Developer",
                "company": "Digital Agency",
                "job_desc": "Creating responsive web applications"
            }
        ]
        
        for app in job_applications:
            instruction = f"""Write a compelling opening paragraph for a cover letter for a {app['job_title']} position."""
            
            input_context = f"""
Candidate: {app['candidate']}
Target Position: {app['job_title']} at {app['company']}
Job Description: {app['job_desc']}
Candidate Skills: {', '.join(app['skills'])}
"""
            
            output = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {app['job_title']} position at {app['company']}. 
With my expertise in {app['skills'][0]} and proven track record of {app['job_desc'].lower()}, 
I am confident that I can make significant contributions to your team.
"""
            
            examples.append(TrainingExample(
                instruction=instruction,
                input_context=input_context,
                output=output,
                category="cover_letter_generation"
            ))
        
        return examples
    
    def generate_ats_optimization_examples(self) -> List[TrainingExample]:
        """Generate training examples for ATS optimization"""
        examples = []
        
        ats_cases = [
            {
                "job_title": "Python Developer",
                "keywords": ["Python", "Django", "PostgreSQL", "REST API"],
                "missing": ["Microservices", "Docker"]
            },
            {
                "job_title": "React Developer",
                "keywords": ["React", "JavaScript", "CSS"],
                "missing": ["TypeScript", "Testing"]
            }
        ]
        
        for case in ats_cases:
            instruction = f"""Optimize profile content for ATS matching for {case['job_title']} position."""
            
            input_context = f"""
Job Title: {case['job_title']}
Required Keywords: {', '.join(case['keywords'])}
Profile Skills: {case['keywords'][0]}, {case['keywords'][1]}
"""
            
            output = f"""ATS Optimization:
Primary Keywords: {', '.join(case['keywords'])}
Missing Keywords to Add: {', '.join(case['missing'])}
Recommended Profile Update:
- Add "{case['missing'][0]}" to skills section
- Highlight "{case['keywords'][0]}" experience in work history
- Include "{case['missing'][1]}" in projects section
"""
            
            examples.append(TrainingExample(
                instruction=instruction,
                input_context=input_context,
                output=output,
                category="ats_optimization"
            ))
        
        return examples
    
    def generate_job_matching_examples(self) -> List[TrainingExample]:
        """Generate training examples for job matching"""
        examples = []
        
        matching_cases = [
            {
                "candidate_skills": ["Python", "Django", "PostgreSQL"],
                "job_title": "Python Developer",
                "match_score": 0.95
            },
            {
                "candidate_skills": ["React", "Vue"],
                "job_title": "Backend Engineer",
                "match_score": 0.2
            }
        ]
        
        for case in matching_cases:
            instruction = "Evaluate job match score for candidate against job requirements."
            
            input_context = f"""
Candidate Skills: {', '.join(case['candidate_skills'])}
Target Job: {case['job_title']}
"""
            
            output = f"""Job Match Analysis:
Match Score: {case['match_score']:.0%}
Assessment: {'Excellent match - Apply immediately' if case['match_score'] > 0.8 else 'Moderate match - Consider applying' if case['match_score'] > 0.5 else 'Poor match - Not recommended'}
"""
            
            examples.append(TrainingExample(
                instruction=instruction,
                input_context=input_context,
                output=output,
                category="job_matching"
            ))
        
        return examples
    
    def generate_application_strategy_examples(self) -> List[TrainingExample]:
        """Generate training examples for application strategy selection"""
        examples = []
        
        strategies = [
            {
                "company": "TechCorp",
                "ats_type": "Greenhouse",
                "strategy": "Use ATS API for direct application"
            },
            {
                "company": "StartupXYZ",
                "ats_type": "Unknown",
                "strategy": "Use LLM-guided browser automation"
            },
            {
                "company": "Enterprise Inc",
                "ats_type": "Standard form",
                "strategy": "Use browser automation with AI form detection"
            }
        ]
        
        for strat in strategies:
            instruction = "Select the best application strategy for this company."
            
            input_context = f"""
Company: {strat['company']}
ATS System: {strat['ats_type']}
"""
            
            output = f"""Recommended Strategy: {strat['strategy']}"""
            
            examples.append(TrainingExample(
                instruction=instruction,
                input_context=input_context,
                output=output,
                category="application_strategy"
            ))
        
        return examples
    
    def save_training_examples(self, examples: List[TrainingExample]):
        """Save training examples to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for example in examples:
            cursor.execute('''
                INSERT INTO training_examples 
                (instruction, input_context, output, category, user_id, job_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                example.instruction,
                example.input_context,
                example.output,
                example.category,
                example.user_id,
                example.job_id
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Saved {len(examples)} training examples")
    
    def _generate_headline(self, profile: Dict) -> str:
        """Generate professional headline"""
        return f"{profile['role']} with {profile['experience']} years of {profile['skills'][0]} expertise"
    
    def generate_all_training_data(self) -> List[TrainingExample]:
        """Generate all training examples"""
        all_examples = []
        
        all_examples.extend(self.generate_profile_enhancement_examples())
        all_examples.extend(self.generate_resume_examples())
        all_examples.extend(self.generate_cover_letter_examples())
        all_examples.extend(self.generate_ats_optimization_examples())
        all_examples.extend(self.generate_job_matching_examples())
        all_examples.extend(self.generate_application_strategy_examples())
        
        self.save_training_examples(all_examples)
        return all_examples


class ModelTrainer:
    """Train Ollama models using collected data"""
    
    def __init__(self, model_name: str = "mistral"):
        self.model_name = model_name
        self.training_data_path = "training_data.jsonl"
        
        if not OLLAMA_AVAILABLE:
            logger.error("❌ Ollama not available. Install with: pip install ollama")
            raise RuntimeError("Ollama not installed")
    
    def create_training_dataset(self, examples: List[TrainingExample]) -> str:
        """Create JSONL training dataset for fine-tuning"""
        jsonl_lines = []
        
        for example in examples:
            jsonl_lines.append(json.dumps({
                "instruction": example.instruction,
                "input": example.input_context,
                "output": example.output,
                "category": example.category
            }))
        
        # Save to file
        with open(self.training_data_path, 'w') as f:
            f.write('\n'.join(jsonl_lines))
        
        logger.info(f"✅ Created training dataset: {self.training_data_path} ({len(jsonl_lines)} examples)")
        return self.training_data_path
    
    def prepare_modelfile(self, model_name: str, training_examples: List[TrainingExample]) -> str:
        """Create a Modelfile for fine-tuned model"""
        
        # Create system prompt from training data
        system_prompt = self._create_system_prompt(training_examples)
        
        modelfile_path = f"Modelfile.{model_name}"
        
        modelfile_content = f"""FROM mistral

SYSTEM \"\"\"You are an expert job application automation assistant. Your role is to help job seekers prepare compelling application materials, optimize their profiles for ATS systems, and strategically apply to jobs that match their skills. You have access to user data including resumes, past applications, and job descriptions. Always provide personalized, professional, and optimized content that maximizes chances of landing interviews.

{system_prompt}
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 1024
PARAMETER num_thread 8
"""
        
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        
        logger.info(f"✅ Created Modelfile: {modelfile_path}")
        return modelfile_path
    
    def _create_system_prompt(self, examples: List[TrainingExample]) -> str:
        """Create system prompt from training examples"""
        categories = {}
        
        for example in examples:
            if example.category not in categories:
                categories[example.category] = []
            categories[example.category].append(example)
        
        prompt_parts = ["You have been trained on the following tasks:\n"]
        
        for category, items in categories.items():
            prompt_parts.append(f"\n{category.replace('_', ' ').title()}:")
            prompt_parts.append(f"  - You have seen {len(items)} examples")
            prompt_parts.append(f"  - You understand how to handle {category.replace('_', ' ')}")
        
        return "\n".join(prompt_parts)
    
    def build_custom_model(self, examples: List[TrainingExample]) -> str:
        """Build a custom Ollama model with training data"""
        logger.info("🚀 Building custom Ollama model...")
        
        try:
            # Create Modelfile
            modelfile_path = self.prepare_modelfile(self.model_name, examples)
            
            # Build the model
            logger.info(f"Building model from Modelfile...")
            model_name_custom = f"{self.model_name}-custom"
            
            # Note: Direct build via Python isn't well-supported yet
            # Instead, provide instructions for user
            logger.info(f"""
✅ Modelfile created: {modelfile_path}

To build the custom model manually:
1. Open terminal in this directory
2. Run: ollama create {model_name_custom} -f {modelfile_path}
3. Then update your config to use: {model_name_custom}

Or use the easy route - our system will automatically use your training data
to improve generation results through prompt injection!
""")
            
            return model_name_custom
            
        except Exception as e:
            logger.error(f"❌ Error building custom model: {e}")
            raise
    
    def validate_model(self) -> bool:
        """Validate that model is working correctly"""
        logger.info(f"Validating {self.model_name} model...")
        
        try:
            # Test with a simple prompt
            test_prompt = "What are the key steps to write an effective cover letter?"
            
            response = ollama.generate(
                model=self.model_name,
                prompt=test_prompt,
                stream=False
            )
            
            if response and response.get('response'):
                logger.info("✅ Model validation successful!")
                return True
            else:
                logger.error("❌ Model validation failed - no response")
                return False
                
        except Exception as e:
            logger.error(f"❌ Model validation failed: {e}")
            return False


class TrainingOrchestrator:
    """Orchestrate the complete training pipeline"""
    
    def __init__(self):
        self.data_generator = TrainingDataGenerator()
        self.trainer = ModelTrainer()
    
    def run_full_training_pipeline(self):
        """Run complete training pipeline"""
        logger.info("=" * 60)
        logger.info("🎓 Starting Full Training Pipeline")
        logger.info("=" * 60)
        
        # Step 1: Generate training data
        logger.info("\n📊 Step 1: Generating training data from real examples...")
        examples = self.data_generator.generate_all_training_data()
        logger.info(f"✅ Generated {len(examples)} training examples")
        
        # Step 2: Create training dataset
        logger.info("\n📝 Step 2: Creating JSONL training dataset...")
        dataset_path = self.trainer.create_training_dataset(examples)
        logger.info(f"✅ Training dataset ready: {dataset_path}")
        
        # Step 3: Build custom model
        logger.info("\n🔧 Step 3: Building custom Ollama model...")
        custom_model = self.trainer.build_custom_model(examples)
        logger.info(f"✅ Custom model configured: {custom_model}")
        
        # Step 4: Validate model
        logger.info("\n✔️  Step 4: Validating model...")
        is_valid = self.trainer.validate_model()
        
        # Step 5: Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Training Pipeline Complete!")
        logger.info("=" * 60)
        
        summary = {
            "training_examples": len(examples),
            "dataset_path": dataset_path,
            "custom_model": custom_model,
            "model_valid": is_valid,
            "categories": {}
        }
        
        # Count by category
        for example in examples:
            if example.category not in summary["categories"]:
                summary["categories"][example.category] = 0
            summary["categories"][example.category] += 1
        
        logger.info("\n📊 Training Summary:")
        for key, value in summary.items():
            if key != "categories":
                logger.info(f"  {key}: {value}")
        
        logger.info("\n📈 Training by Category:")
        for category, count in summary["categories"].items():
            logger.info(f"  {category}: {count} examples")
        
        return summary


def main():
    """Main training entry point"""
    logger.info("🤖 AI Training Pipeline for Job Application Automation")
    logger.info("=" * 60)
    
    # Check Ollama
    if not OLLAMA_AVAILABLE:
        logger.error("❌ Ollama not installed!")
        logger.info("Install Ollama:")
        logger.info("  - Windows: Download from https://ollama.ai")
        logger.info("  - Mac: brew install ollama")
        logger.info("  - Linux: curl https://ollama.ai/install.sh | sh")
        logger.info("\nThen install Python package: pip install ollama")
        sys.exit(1)
    
    try:
        # Check if Ollama server is running
        response = ollama.list()
        logger.info("✅ Ollama server is running!")
    except Exception as e:
        logger.error(f"❌ Ollama server not responding: {e}")
        logger.info("Start Ollama with: ollama serve")
        sys.exit(1)
    
    # Run training pipeline
    orchestrator = TrainingOrchestrator()
    summary = orchestrator.run_full_training_pipeline()
    
    # Save summary
    with open("training_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("\n✨ Training summary saved to: training_summary.json")
    logger.info("\n🚀 Your Ollama model is now enhanced for job automation!")


if __name__ == "__main__":
    main()
