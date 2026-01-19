"""
Main entry point for the RAG-based Q&A system.
Supports both command-line arguments and interactive mode.
"""

import argparse
import sys
from config import Config
from rag_engine import RagEngine
from logger import setup_logger

logger = setup_logger(name="RAG_pipeline", log_level="INFO")


def main():
    """Main function to run the RAG Q&A system."""
    parser = argparse.ArgumentParser(
        description="RAG-based Q&A System for Company Policies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Can I work from home?"
  python main.py --question "What's on the cafeteria menu?"
  python main.py --interactive
        """
    )
    
    parser.add_argument(
        'question',
        nargs='?',
        help='Question to ask the system'
    )
    
    parser.add_argument(
        '-q', '--question',
        dest='question_flag',
        help='Question to ask the system (alternative syntax)'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--ingest',
        action='store_true',
        help='For ingestion of documents'
    )

    parser.add_argument(
        '-f', '--full',
        action='store_true',
        help='Show full detailed final answer (default: compact)'
    )
    
    args = parser.parse_args()
    question = args.question or args.question_flag
    has_action = args.ingest or args.interactive or question
    
    if not has_action:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Initialize configuration and RAG engine
        config = Config()
        rag = RagEngine(config)
        
        # Load or ingest documents
        if args.ingest:
            logger.info("ingesting documents...")
            rag.ingest_documents()
            print("\n   Documents ingested successfully!\n")
            # If only --ingest was passed, exit after ingestion
            if not args.interactive and not (args.question or args.question_flag):
                sys.exit(0)
        else:
            try:
                rag.load_vectorstore()
                logger.info("Vector store loaded successfully")
            except FileNotFoundError:
                logger.warning("Vector store not found. Ingesting documents...")
                rag.ingest_documents()
        
        # Determine question source
        
        compact = not args.full
        
        if args.interactive:
            run_interactive_mode(rag, compact=compact)
        elif question:
            answer = process_question(rag, question)
            print_answer(question, answer, compact=compact)
        else:
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n  Error: {e}")
        sys.exit(1)


def run_interactive_mode(rag: RagEngine):
    """Run the system in interactive mode."""
    print("\n" + "=" * 70)
    print("   RAG Q&A SYSTEM - Interactive Mode")
    print("=" * 70)
    print("Type your questions below. Type 'exit', 'quit', or 'q' to stop.\n")
    
    while True:
        try:
            question = input("  Your question: ").strip()
            
            if question.lower() in ['exit', 'quit', 'q', '']:
                print("\n👋 Goodbye!\n")
                break
            
            answer = process_question(rag, question)
            print_answer(question, answer, compact=True)
            print()  # Add spacing between Q&A pairs
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            print(f"\n  Error: {e}\n")


def process_question(rag: RagEngine, question: str):
    """Process a single question through the RAG engine."""
    logger.info(f"Processing question: {question}")
    answer = rag.query(question)
    return answer


def print_answer(question: str, answer, compact: bool = True):
    """Print the answer in a formatted way."""
    if compact:
        print("\n" + "-" * 70)
        print(f"    Answer: {answer.answer}")
        print(f"    Sources: {', '.join(answer.cited_sources)}")
        print("-" * 70)
    else:
        print("\n" + "=" * 70)
        print("   QUESTION:")
        print("=" * 70)
        print(f"\n{question}\n")
        print("=" * 70)
        print("   ANSWER:")
        print("=" * 70)
        print(f"\n{answer.answer}\n")
        print("-" * 70)
        print("   DETAILS:")
        print("-" * 70)
        print(f"Reasoning: {answer.reasoning}")
        print(f"Sources: {', '.join(answer.cited_sources)}")
        print(f"Policy allows remote: {answer.policy_allows_remote}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()