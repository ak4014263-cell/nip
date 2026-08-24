"""
Real User Data Collection System
Collects resumes, applications, feedback, and outcomes to continuously improve model
"""

import json
import os
import sqlite3
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserDataCollector:
    """Collect and organize real user data for training"""
    
    def __init__(self, db_path: str = "user_data.db"):
        self.db_path = db_path
        self.resumes_dir = Path("user_resumes")
        self.applications_dir = Path("user_applications")
        self.setup()
    
    def setup(self):
        """Initialize directories and database"""
        self.resumes_dir.mkdir(exist_ok=True)
        self.applications_dir.mkdir(exist_ok=True)
        self.setup_database()
    
    def setup_database(self):
        """Setup SQLite database for user data tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                skills TEXT,
                experience_years INTEGER,
                bio TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_resumes (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                resume_text TEXT,
                skills TEXT,
                experience_years INTEGER,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES user_profiles(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                job_title TEXT,
                company TEXT,
                job_url TEXT UNIQUE,
                job_description TEXT,
                user_skills TEXT,
                generated_resume_section TEXT,
                generated_cover_letter TEXT,
                generated_profile_text TEXT,
                application_status TEXT,
                received_response BOOLEAN DEFAULT 0,
                interview_invited BOOLEAN DEFAULT 0,
                offer_received BOOLEAN DEFAULT 0,
                feedback_score FLOAT DEFAULT 0.5,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                response_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES user_profiles(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_performance_feedback (
                id INTEGER PRIMARY KEY,
                application_id INTEGER,
                metric_name TEXT,
                metric_value FLOAT,
                feedback_type TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(application_id) REFERENCES job_applications(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_effectiveness (
                id INTEGER PRIMARY KEY,
                metric_name TEXT,
                metric_value FLOAT,
                date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ User data database initialized")
    
    def collect_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Collect and store user profile data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_id, name, email, skills, experience_years, bio, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}",
                profile_data.get('email'),
                json.dumps(profile_data.get('skills', [])),
                profile_data.get('experience_years', 0),
                profile_data.get('bio', '')
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Collected profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to collect profile: {e}")
            return False
    
    def collect_resume(self, user_id: str, resume_text: str, extracted_data: Dict) -> bool:
        """Store uploaded resume and extracted data"""
        try:
            # Save resume text to file
            resume_hash = hashlib.md5(f"{user_id}_{datetime.now()}".encode()).hexdigest()[:8]
            resume_file = self.resumes_dir / f"{user_id}_{resume_hash}.txt"
            
            with open(resume_file, 'w', encoding='utf-8') as f:
                f.write(resume_text)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_resumes 
                (user_id, resume_text, skills, experience_years)
                VALUES (?, ?, ?, ?)
            ''', (
                user_id,
                resume_text,
                json.dumps(extracted_data.get('skills', [])),
                extracted_data.get('experience_years', 0)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Collected resume for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to collect resume: {e}")
            return False
    
    def log_job_application(self, user_id: str, job_data: Dict, generated_content: Dict) -> int:
        """Log job application with AI-generated content"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO job_applications
                (user_id, job_title, company, job_url, job_description, 
                 user_skills, generated_resume_section, generated_cover_letter,
                 generated_profile_text, application_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('url', ''),
                job_data.get('description', ''),
                json.dumps(job_data.get('user_skills', [])),
                generated_content.get('resume_section', ''),
                generated_content.get('cover_letter', ''),
                generated_content.get('profile_text', ''),
                'applied'
            ))
            
            application_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Logged application {application_id} for {job_data.get('title')} at {job_data.get('company')}")
            return application_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log application: {e}")
            return -1
    
    def update_application_outcome(self, application_id: int, outcome: Dict) -> bool:
        """Update application with outcome (response, interview, offer)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE job_applications
                SET received_response = ?, 
                    interview_invited = ?,
                    offer_received = ?,
                    application_status = ?,
                    response_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                1 if outcome.get('received_response') else 0,
                1 if outcome.get('interview_invited') else 0,
                1 if outcome.get('offer_received') else 0,
                outcome.get('status', 'responded'),
                application_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Updated application {application_id} outcome")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update outcome: {e}")
            return False
    
    def record_ai_feedback(self, application_id: int, metrics: Dict, notes: str = "") -> bool:
        """Record feedback on AI-generated content performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate overall feedback score
            scores = list(metrics.values())
            avg_score = sum(scores) / len(scores) if scores else 0.5
            
            # Record each metric
            for metric_name, metric_value in metrics.items():
                cursor.execute('''
                    INSERT INTO ai_performance_feedback
                    (application_id, metric_name, metric_value, feedback_type, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    application_id,
                    metric_name,
                    metric_value,
                    'quality_rating',
                    notes
                ))
            
            # Update application feedback score
            cursor.execute('''
                UPDATE job_applications SET feedback_score = ? WHERE id = ?
            ''', (avg_score, application_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Recorded feedback for application {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to record feedback: {e}")
            return False
    
    def get_training_dataset(self) -> List[Dict]:
        """Extract training dataset from collected data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    ja.job_title, ja.job_description, ja.user_skills,
                    ja.generated_cover_letter, ja.generated_resume_section,
                    ja.received_response, ja.interview_invited, ja.offer_received,
                    ja.feedback_score
                FROM job_applications ja
                WHERE ja.received_response = 1 OR ja.feedback_score > 0
            ''')
            
            dataset = []
            for row in cursor.fetchall():
                dataset.append({
                    'job_title': row[0],
                    'job_description': row[1],
                    'user_skills': json.loads(row[2]) if row[2] else [],
                    'cover_letter': row[3],
                    'resume_section': row[4],
                    'received_response': bool(row[5]),
                    'interview_invited': bool(row[6]),
                    'offer_received': bool(row[7]),
                    'quality_score': row[8]
                })
            
            conn.close()
            logger.info(f"✅ Extracted {len(dataset)} training examples from real applications")
            return dataset
            
        except Exception as e:
            logger.error(f"❌ Failed to extract training dataset: {e}")
            return []
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics from collected data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total applications
            cursor.execute('SELECT COUNT(*) FROM job_applications')
            stats['total_applications'] = cursor.fetchone()[0]
            
            # Response rate
            cursor.execute('SELECT COUNT(*) FROM job_applications WHERE received_response = 1')
            stats['responses'] = cursor.fetchone()[0]
            stats['response_rate'] = stats['responses'] / max(stats['total_applications'], 1)
            
            # Interview rate
            cursor.execute('SELECT COUNT(*) FROM job_applications WHERE interview_invited = 1')
            stats['interviews'] = cursor.fetchone()[0]
            stats['interview_rate'] = stats['interviews'] / max(stats['total_applications'], 1)
            
            # Offer rate
            cursor.execute('SELECT COUNT(*) FROM job_applications WHERE offer_received = 1')
            stats['offers'] = cursor.fetchone()[0]
            stats['offer_rate'] = stats['offers'] / max(stats['total_applications'], 1)
            
            # Average AI quality score
            cursor.execute('SELECT AVG(feedback_score) FROM job_applications')
            stats['avg_ai_quality'] = cursor.fetchone()[0] or 0.5
            
            # Users
            cursor.execute('SELECT COUNT(*) FROM user_profiles')
            stats['total_users'] = cursor.fetchone()[0]
            
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get performance stats: {e}")
            return {}


class ContinuousLearning:
    """Continuous learning system - improves model over time"""
    
    def __init__(self, db_path: str = "user_data.db"):
        self.db_path = db_path
        self.collector = UserDataCollector(db_path)
    
    def analyze_successful_applications(self) -> Dict:
        """Analyze what makes applications successful"""
        try:
            dataset = self.collector.get_training_dataset()
            
            successful = [d for d in dataset if d.get('offer_received') or d.get('interview_invited')]
            failed = [d for d in dataset if not d.get('received_response')]
            
            analysis = {
                "total_analyzed": len(dataset),
                "successful_count": len(successful),
                "success_rate": len(successful) / max(len(dataset), 1),
                "insights": []
            }
            
            if successful:
                # Extract common patterns from successful applications
                analysis["insights"].append({
                    "pattern": "Successful applications",
                    "count": len(successful),
                    "avg_quality": sum(d.get('quality_score', 0.5) for d in successful) / len(successful)
                })
            
            if failed:
                analysis["insights"].append({
                    "pattern": "Failed applications",
                    "count": len(failed),
                    "recommendation": "Improve cover letter quality and skill matching"
                })
            
            logger.info(f"✅ Analyzed {len(dataset)} applications: {analysis['success_rate']:.1%} success rate")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze applications: {e}")
            return {}
    
    def identify_model_weaknesses(self) -> List[str]:
        """Identify areas where AI model performs poorly"""
        weaknesses = []
        
        try:
            stats = self.collector.get_performance_stats()
            
            if stats.get('response_rate', 0) < 0.3:
                weaknesses.append("Low response rate - improve cover letter quality")
            
            if stats.get('interview_rate', 0) < 0.1:
                weaknesses.append("Low interview rate - better skill highlighting needed")
            
            if stats.get('avg_ai_quality', 0.5) < 0.6:
                weaknesses.append("Low content quality scores - retrain model")
            
            logger.info(f"✅ Identified {len(weaknesses)} model improvement areas")
            return weaknesses
            
        except Exception as e:
            logger.error(f"❌ Failed to identify weaknesses: {e}")
            return []
    
    def generate_improvement_report(self) -> Dict:
        """Generate report on model performance and recommendations"""
        return {
            "timestamp": datetime.now().isoformat(),
            "performance": self.collector.get_performance_stats(),
            "analysis": self.analyze_successful_applications(),
            "weaknesses": self.identify_model_weaknesses(),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for model improvement"""
        recommendations = []
        
        stats = self.collector.get_performance_stats()
        
        if stats.get('response_rate', 0) < 0.4:
            recommendations.append("Add more personalization to cover letters")
        
        if stats.get('interview_rate', 0) < 0.15:
            recommendations.append("Improve ATS keyword matching in resumes")
        
        if stats.get('total_applications', 0) < 100:
            recommendations.append("Collect more training data (100+ applications) for better model training")
        
        recommendations.append("Regularly collect feedback on generated content quality")
        recommendations.append("Monitor which job titles have highest success rates")
        
        return recommendations


def demonstrate_data_collection():
    """Demonstrate data collection workflow"""
    logger.info("🎓 Data Collection System Demonstration")
    logger.info("=" * 60)
    
    collector = UserDataCollector()
    learning = ContinuousLearning()
    
    # Example: Simulate user data collection
    logger.info("\n1. Collecting user profile...")
    collector.collect_user_profile("user_001", {
        "first_name": "John",
        "last_name": "Developer",
        "email": "john@example.com",
        "skills": ["Python", "React", "AWS"],
        "experience_years": 5,
        "bio": "Full-stack developer with cloud expertise"
    })
    
    logger.info("\n2. Collecting user resume...")
    resume_text = """
John Developer - Senior Full Stack Developer
john@example.com | +33 6 12 34 56 78

EXPERIENCE:
TechCorp - Senior Developer (2021-Present)
- Led migration to microservices architecture
- Implemented CI/CD pipelines

StartupXYZ - Full Stack Developer (2018-2021)
- Built React frontend and Node.js backend
- Scaled application to 100k users

SKILLS:
Python, JavaScript, React, Node.js, AWS, Docker, PostgreSQL
"""
    collector.collect_resume("user_001", resume_text, {
        "skills": ["Python", "React", "AWS"],
        "experience_years": 5
    })
    
    logger.info("\n3. Logging job applications...")
    app_id = collector.log_job_application("user_001", {
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "url": "https://techcorp.com/jobs/senior-python",
        "description": "We seek a Senior Python Developer...",
        "user_skills": ["Python", "AWS"]
    }, {
        "resume_section": "Experienced Python developer with 5 years...",
        "cover_letter": "I am writing to express...",
        "profile_text": "Senior full-stack developer..."
    })
    
    logger.info("\n4. Recording outcomes...")
    if app_id > 0:
        collector.update_application_outcome(app_id, {
            "received_response": True,
            "interview_invited": True,
            "offer_received": False,
            "status": "interview_scheduled"
        })
        
        logger.info("\n5. Recording AI feedback...")
        collector.record_ai_feedback(app_id, {
            "resume_quality": 0.8,
            "cover_letter_quality": 0.75,
            "skill_matching": 0.9,
            "personalization": 0.7
        }, "Good match but cover letter could be more specific")
    
    logger.info("\n6. Performance Analysis...")
    report = learning.generate_improvement_report()
    logger.info("\n📊 Improvement Report:")
    logger.info(json.dumps(report, indent=2))
    
    logger.info("\n✨ Data Collection System Ready!")
    logger.info("This system continuously learns from real applications to improve AI quality")


if __name__ == "__main__":
    demonstrate_data_collection()
