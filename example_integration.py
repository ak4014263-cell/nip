#!/usr/bin/env python3
"""
Example Integration: How to use the anti-bot solution in your existing code
"""
import asyncio
import sys
import os
import logging

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'automation', 'app'))

from adapters.wttj_enhanced_adapter import WTTJEnhancedAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_1_create_account():
    """
    Example 1: Create a WTTJ account
    Uses intelligent routing (API first, then stealth browser)
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Create WTTJ Account")
    print("="*80 + "\n")
    
    # Initialize adapter
    adapter = WTTJEnhancedAdapter(
        api_key=os.getenv('WTTJ_API_KEY'),  # Optional - falls back to browser if not set
        use_stealth=True,
        headless=False  # Set True for production
    )
    
    try:
        # Account details
        import time
        import uuid
        
        timestamp = int(time.time())
        test_email = f"test_user_{timestamp}@example.com"
        test_password = f"SecurePass{uuid.uuid4().hex[:8]}!"
        
        logger.info(f"Creating account for: {test_email}")
        
        # Create account - adapter automatically selects best method
        result = await adapter.create_account(
            email=test_email,
            password=test_password,
            first_name="John",
            last_name="Developer",
            phone="+33612345678"
        )
        
        if result["success"]:
            logger.info("✅ Account created successfully!")
            logger.info(f"   Method used: {result.get('method')}")
            logger.info(f"   Email: {test_email}")
            logger.info(f"   Password: {test_password}")
            return result
        else:
            logger.error(f"❌ Account creation failed: {result.get('error')}")
            return result
            
    finally:
        await adapter.close()


async def example_2_search_jobs():
    """
    Example 2: Search for jobs
    Uses Algolia direct access (fastest, no auth needed)
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Search Jobs")
    print("="*80 + "\n")
    
    adapter = WTTJEnhancedAdapter()
    
    try:
        logger.info("Searching for Python Developer jobs in Paris...")
        
        # Search jobs - automatically uses Algolia
        result = await adapter.search_jobs(
            query="Python Developer",
            location="Paris",
            per_page=10
        )
        
        if result["success"]:
            total = result.get('total_results', 0)
            jobs = result.get('jobs', [])
            
            logger.info(f"✅ Found {total} jobs")
            logger.info("\nTop 5 results:")
            
            for i, job in enumerate(jobs[:5], 1):
                title = job.get('name', 'Unknown')
                company = job.get('organization', {}).get('name', 'Unknown')
                location = job.get('office', {}).get('name', 'Unknown')
                logger.info(f"  {i}. {title}")
                logger.info(f"     Company: {company}")
                logger.info(f"     Location: {location}\n")
            
            return jobs
        else:
            logger.error(f"❌ Job search failed: {result.get('error')}")
            return []
            
    finally:
        await adapter.close()


async def example_3_apply_to_job():
    """
    Example 3: Apply to a job
    Uses API if possible, falls back to stealth browser
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Apply to Job")
    print("="*80 + "\n")
    
    # First, search for a job
    adapter = WTTJEnhancedAdapter(
        api_key=os.getenv('WTTJ_API_KEY'),
        use_stealth=True,
        headless=False
    )
    
    try:
        # Search for jobs
        logger.info("Searching for jobs to apply to...")
        search_result = await adapter.search_jobs(
            query="Python",
            location="Paris",
            per_page=5
        )
        
        if not search_result["success"] or not search_result.get('jobs'):
            logger.error("No jobs found")
            return
        
        # Get first job
        job = search_result['jobs'][0]
        job_title = job.get('name', 'Unknown')
        job_company = job.get('organization', {}).get('name', 'Unknown')
        job_url = f"https://www.welcometothejungle.com/en/companies/{job.get('organization', {}).get('slug')}/jobs/{job.get('slug')}"
        
        logger.info(f"\nApplying to: {job_title} at {job_company}")
        logger.info(f"URL: {job_url}")
        
        # Prepare application
        cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {job_company}.

With extensive experience in Python development and a passion for building scalable applications, 
I believe I would be a great fit for your team.

I am excited about the opportunity to contribute to your projects and would love to discuss 
how my skills align with your needs.

Best regards,
John Developer"""
        
        # Apply - adapter automatically selects best method
        result = await adapter.apply_to_job(
            job_url=job_url,
            email="john.developer@example.com",
            first_name="John",
            last_name="Developer",
            phone="+33612345678",
            cover_letter=cover_letter,
            resume_url="https://example.com/resume.pdf"
        )
        
        if result["success"]:
            logger.info("✅ Application submitted successfully!")
            logger.info(f"   Method used: {result.get('method')}")
            return result
        else:
            logger.error(f"❌ Application failed: {result.get('error')}")
            return result
            
    finally:
        await adapter.close()


async def example_4_full_workflow():
    """
    Example 4: Full workflow
    Create account → Search jobs → Apply to multiple jobs
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Full Automation Workflow")
    print("="*80 + "\n")
    
    adapter = WTTJEnhancedAdapter(
        api_key=os.getenv('WTTJ_API_KEY'),
        use_stealth=True,
        headless=False
    )
    
    try:
        # Step 1: Create account
        logger.info("STEP 1: Creating account...")
        import time
        import uuid
        
        timestamp = int(time.time())
        email = f"candidate_{timestamp}@example.com"
        password = f"Pass{uuid.uuid4().hex[:10]}!"
        
        account_result = await adapter.create_account(
            email=email,
            password=password,
            first_name="Jane",
            last_name="Candidate",
            phone="+33612345678"
        )
        
        if not account_result["success"]:
            logger.error("Account creation failed, stopping workflow")
            return
        
        logger.info("✅ Account created\n")
        await asyncio.sleep(2)
        
        # Step 2: Search for relevant jobs
        logger.info("STEP 2: Searching for relevant jobs...")
        jobs_result = await adapter.search_jobs(
            query="Python Developer",
            location="Paris",
            per_page=5
        )
        
        if not jobs_result["success"]:
            logger.error("Job search failed")
            return
        
        jobs = jobs_result.get('jobs', [])
        logger.info(f"✅ Found {len(jobs)} jobs\n")
        await asyncio.sleep(2)
        
        # Step 3: Apply to top 3 jobs
        logger.info("STEP 3: Applying to top jobs...")
        applications = []
        
        for i, job in enumerate(jobs[:3], 1):
            job_title = job.get('name', 'Unknown')
            company = job.get('organization', {}).get('name', 'Unknown')
            
            logger.info(f"\n[{i}/3] Applying to: {job_title} at {company}")
            
            job_url = f"https://www.welcometothejungle.com/en/companies/{job.get('organization', {}).get('slug')}/jobs/{job.get('slug')}"
            
            result = await adapter.apply_to_job(
                job_url=job_url,
                email=email,
                first_name="Jane",
                last_name="Candidate",
                phone="+33612345678",
                cover_letter=f"I am very interested in the {job_title} position at {company}."
            )
            
            applications.append({
                'job': job_title,
                'company': company,
                'success': result.get('success', False)
            })
            
            await asyncio.sleep(3)  # Delay between applications
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("WORKFLOW COMPLETE")
        logger.info("="*80)
        logger.info(f"\n✅ Account created: {email}")
        logger.info(f"✅ Jobs found: {len(jobs)}")
        logger.info(f"✅ Applications submitted: {len(applications)}")
        
        logger.info("\nApplication Results:")
        for i, app in enumerate(applications, 1):
            status = "✅ Success" if app['success'] else "❌ Failed"
            logger.info(f"  {i}. {app['job']} at {app['company']} - {status}")
        
        logger.info("\n" + "="*80 + "\n")
        
    finally:
        await adapter.close()


async def main():
    """Main menu"""
    print("\n" + "="*80)
    print("🚀 ANTI-BOT SOLUTION - INTEGRATION EXAMPLES")
    print("="*80)
    print("\nChoose an example to run:")
    print("\n1. Create WTTJ Account")
    print("2. Search for Jobs")
    print("3. Apply to a Job")
    print("4. Full Workflow (Create + Search + Apply)")
    print("0. Exit")
    print("\n" + "="*80)
    
    choice = input("\nEnter your choice (0-4): ").strip()
    
    try:
        if choice == '1':
            await example_1_create_account()
        elif choice == '2':
            await example_2_search_jobs()
        elif choice == '3':
            await example_3_apply_to_job()
        elif choice == '4':
            await example_4_full_workflow()
        elif choice == '0':
            print("\n👋 Goodbye!")
            return
        else:
            print("\n❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("Example complete!")
    print("="*80 + "\n")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
