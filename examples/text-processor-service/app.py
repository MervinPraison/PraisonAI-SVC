"""Example Text Processing Service Application.

This service demonstrates the PraisonAI Service Framework by:
- Processing text input (uppercase, lowercase, word count, etc.)
- Generating formatted output files
- Using the @app.job decorator pattern
- Handling various text transformations
"""

import json
from datetime import datetime
from dotenv import load_dotenv

from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

# Initialize the service
app = ServiceApp("Text Processor Service")


@app.job
def process_text(payload: dict) -> tuple[bytes, str, str]:
    """Process text based on the requested operation.

    Args:
        payload: Job payload containing:
            - text (str): The text to process
            - operation (str): Type of operation (uppercase, lowercase, reverse, stats, all)
            - format (str): Output format (txt, json, md) - default: txt

    Returns:
        tuple of (file_data, content_type, filename)
    
    Example payload:
        {
            "text": "Hello World!",
            "operation": "all",
            "format": "json"
        }
    """
    # Extract parameters
    text = payload.get("text", "")
    operation = payload.get("operation", "stats").lower()
    output_format = payload.get("format", "txt").lower()
    
    if not text:
        raise ValueError("Text is required in payload")
    
    # Process text based on operation
    results = {}
    
    if operation in ["uppercase", "all"]:
        results["uppercase"] = text.upper()
    
    if operation in ["lowercase", "all"]:
        results["lowercase"] = text.lower()
    
    if operation in ["reverse", "all"]:
        results["reverse"] = text[::-1]
    
    if operation in ["stats", "all"]:
        results["stats"] = {
            "char_count": len(text),
            "word_count": len(text.split()),
            "line_count": text.count('\n') + 1,
            "unique_words": len(set(text.lower().split()))
        }
    
    if operation == "title":
        results["title_case"] = text.title()
    
    if operation == "count_vowels":
        vowels = "aeiouAEIOU"
        results["vowel_count"] = sum(1 for char in text if char in vowels)
    
    # Generate output based on format
    timestamp = datetime.utcnow().isoformat()
    
    if output_format == "json":
        output_data = {
            "original_text": text,
            "operation": operation,
            "results": results,
            "processed_at": timestamp
        }
        file_data = json.dumps(output_data, indent=2).encode('utf-8')
        content_type = "application/json"
        filename = f"text_processing_{timestamp[:10]}.json"
    
    elif output_format == "md":
        lines = [
            "# Text Processing Results",
            f"\n**Processed:** {timestamp}",
            f"\n**Operation:** {operation}",
            "\n## Original Text",
            f"\n```\n{text}\n```",
            "\n## Results\n"
        ]
        
        for key, value in results.items():
            if key == "stats":
                lines.append("\n### Statistics")
                for stat_key, stat_value in value.items():
                    lines.append(f"- **{stat_key.replace('_', ' ').title()}:** {stat_value}")
            else:
                lines.append(f"\n### {key.replace('_', ' ').title()}")
                lines.append(f"\n```\n{value}\n```")
        
        file_data = "\n".join(lines).encode('utf-8')
        content_type = "text/markdown"
        filename = f"text_processing_{timestamp[:10]}.md"
    
    else:  # txt format
        lines = [
            "=" * 60,
            "TEXT PROCESSING RESULTS",
            "=" * 60,
            f"\nProcessed: {timestamp}",
            f"Operation: {operation}",
            "\n" + "-" * 60,
            "ORIGINAL TEXT",
            "-" * 60,
            text,
            "\n" + "-" * 60,
            "RESULTS",
            "-" * 60
        ]
        
        for key, value in results.items():
            lines.append(f"\n{key.upper()}:")
            if isinstance(value, dict):
                for stat_key, stat_value in value.items():
                    lines.append(f"  {stat_key}: {stat_value}")
            else:
                lines.append(f"  {value}")
        
        lines.append("\n" + "=" * 60)
        
        file_data = "\n".join(lines).encode('utf-8')
        content_type = "text/plain"
        filename = f"text_processing_{timestamp[:10]}.txt"
    
    return file_data, content_type, filename


if __name__ == "__main__":
    print("🚀 Starting Text Processor Service...")
    print("📝 Service URL: http://localhost:8080")
    print("💡 Use POST /jobs to create jobs")
    print("❤️  Use GET /health for health check")
    app.run(host="0.0.0.0", port=8080)

