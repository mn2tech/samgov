"""
Simple runner script for the AI Contract Finder.
Supports both Streamlit UI and FastAPI backend.
"""
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="AI Contract Finder Runner")
    parser.add_argument(
        "--mode",
        choices=["streamlit", "api"],
        default="streamlit",
        help="Run mode: streamlit (UI) or api (REST API)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port number (default: 8501 for Streamlit, 8000 for API)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "streamlit":
        import subprocess
        port = args.port or 8501
        cmd = ["streamlit", "run", "app.py", "--server.port", str(port)]
        print(f"Starting Streamlit UI on port {port}...")
        subprocess.run(cmd)
    
    elif args.mode == "api":
        import uvicorn
        port = args.port or 8000
        print(f"Starting FastAPI backend on port {port}...")
        uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()
