"""
EvalMate: Intelligent Student Assignment Feedback System

Main entry point for initializing the application and verifying
the environment setup.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_directories_exist, get_config, STORAGE_MODE
from core.store.sqlite_store import init_db


def main():
    """
    Initialize the EvalMate application.
    
    This function sets up the necessary directories and database
    to prepare the application for use.
    """
    print("🚀 Initializing EvalMate...")
    print("=" * 50)
    
    try:
        # Ensure all data directories exist
        print("📁 Setting up data directories...")
        ensure_directories_exist()
        
        # Initialize SQLite database
        print("🗄️  Initializing database...")
        init_db()
        
        # Display configuration summary
        config = get_config()
        print("\n📋 Configuration Summary:")
        print(f"   Storage Mode: {STORAGE_MODE}")
        print(f"   Data Directory: {config['data_dir']}")
        print(f"   Database Path: {config['database_path']}")
        
        print("\n✅ Project initialized successfully!")
        print("   Data folders and SQLite database are ready.")
        print("   You can now start building your evaluation system.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        return False


def verify_setup():
    """
    Verify that the setup completed successfully.
    
    Returns:
        True if setup is valid, False otherwise
    """
    from config import DATA_DIR, DATABASE_PATH, DIRECTORIES
    
    print("\n🔍 Verifying setup...")
    
    # Check if data directories exist
    missing_dirs = []
    for name, path in DIRECTORIES.items():
        if not path.exists():
            missing_dirs.append(f"{name} ({path})")
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    # Check if database exists
    if not DATABASE_PATH.exists():
        print(f"❌ Database not found: {DATABASE_PATH}")
        return False
    
    print("✅ Setup verification passed!")
    return True


def test_repository():
    """
    Test repository functionality with a sample rubric.
    
    Returns:
        True if test passes, False otherwise
    """
    try:
        from core.models.schemas import Rubric, RubricItem, CanonicalDoc, DocBlock, RubricCriterion
        from core.store.repo import save_rubric, list_rubrics, get_rubric
        from core.models.ids import new_rubric_id, new_doc_id, new_block_id
        from datetime import datetime
        
        print("   Creating sample rubric...")
        
        # Create a sample rubric
        rubric = Rubric(
            id=new_rubric_id(),
            course="CS101",
            assignment="Assignment 1",
            version="v1.0",
            items=[
                RubricItem(
                    id=new_block_id(),  # Use proper ID format
                    title="Code Quality",
                    description="Evaluate code structure and style",
                    weight=0.4,
                    criterion=RubricCriterion.STRUCTURE
                ),
                RubricItem(
                    id=new_block_id(),  # Use proper ID format
                    title="Correctness",
                    description="Verify solution correctness",
                    weight=0.6,
                    criterion=RubricCriterion.ACCURACY
                )
            ],
            canonical=CanonicalDoc(
                id=new_doc_id(),
                title="Sample Rubric Document",
                source_files=["sample_rubric.pdf"],  # Must have at least one source file
                blocks=[
                    DocBlock(
                        id=new_block_id(),
                        kind="text",
                        text="This is a sample rubric for testing purposes.",
                        page=1,
                        bbox=None
                    )
                ],
                created_at=datetime.utcnow()
            )
        )
        
        # Test save operation
        print(f"   Saving rubric: {rubric.id}")
        saved_id = save_rubric(rubric)
        assert saved_id == rubric.id, f"Save returned wrong ID: {saved_id}"
        
        # Test list operation
        print("   Listing rubrics...")
        rubrics = list_rubrics()
        assert len(rubrics) >= 1, "No rubrics found after save"
        assert any(r['id'] == rubric.id for r in rubrics), "Saved rubric not in list"
        
        # Test retrieve operation
        print(f"   Retrieving rubric: {rubric.id}")
        retrieved = get_rubric(rubric.id)
        assert retrieved.id == rubric.id, "Retrieved rubric has wrong ID"
        assert retrieved.course == rubric.course, "Retrieved rubric has wrong course"
        assert len(retrieved.items) == len(rubric.items), "Retrieved rubric has wrong number of items"
        
        print("   ✅ All repository operations successful!")
        return True
        
    except Exception as e:
        print(f"   ❌ Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Initialize the project
    success = main()
    
    if success:
        # Verify the setup
        verify_setup()
        
        # Run repository smoke test
        print("\n🧪 Running repository smoke test...")
        test_success = test_repository()
        
        if test_success:
            print("✅ Repository smoke test passed!")
        else:
            print("❌ Repository smoke test failed!")
            
        print("\n🎯 Next Steps:")
        print("   1. Review the project structure")
        print("   2. Run tests: python -m pytest app/tests/")
        print("   3. Start implementing business logic")
        print("   4. Add your first rubric and questions")
        
    else:
        print("\n💡 Please fix the errors above and try again.")
        sys.exit(1)