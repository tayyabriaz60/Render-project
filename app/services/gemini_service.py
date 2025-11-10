"""
Gemini AI service for analyzing medical feedback
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from app.utils.prompts import get_analysis_prompt
from app.utils.helpers import (
    parse_json_safely,
    extract_urgency_level,
    extract_urgency_reason,
    extract_urgency_flags,
    extract_categories,
    extract_medical_concerns,
    format_error_response
)

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


class GeminiService:
    """Service for interacting with Gemini AI"""
    
    def __init__(self):
        self.model = None
        if GOOGLE_API_KEY:
            try:
                # Using gemini-2.5-flash (newest, balanced performance)
                # Alternatives: 'gemini-1.5-pro' (better quality) or 'gemini-1.5-flash' (faster)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"Error initializing Gemini 2.5 Flash model: {e}")
                # Fallback to gemini-1.5-flash if 2.5-flash not available
                try:
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                    print("Using fallback model: gemini-1.5-flash")
                except Exception as e2:
                    print(f"Error with fallback model: {e2}")
                    # Final fallback to gemini-pro
                    try:
                        self.model = genai.GenerativeModel('gemini-pro')
                        print("Using final fallback model: gemini-pro")
                    except:
                        pass
    
    async def analyze_feedback(
        self,
        feedback_text: str,
        department: str,
        doctor_name: Optional[str] = None,
        visit_date: Optional[str] = None,
        rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze feedback using Gemini AI
        
        Returns:
            Dict containing analysis results or error information
        """
        if not self.model:
            error_msg = "Gemini API not configured. Please set GOOGLE_API_KEY in .env"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg
            }
        
        try:
            # Generate prompt
            prompt = get_analysis_prompt(
                feedback_text=feedback_text,
                department=department,
                doctor_name=doctor_name,
                visit_date=visit_date,
                rating=rating
            )
            
            # Run Gemini API call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Extract text from response
            response_text = response.text if hasattr(response, 'text') else str(response)
            print(f"📥 Gemini API Response received (length: {len(response_text)} chars)")
            
            # Parse JSON response
            analysis_data = parse_json_safely(response_text)
            
            if analysis_data:
                print(f"✅ Successfully parsed Gemini response")
                print(f"   Sentiment: {analysis_data.get('sentiment')}, Urgency: {analysis_data.get('urgency', {}).get('level') if isinstance(analysis_data.get('urgency'), dict) else 'N/A'}")
            else:
                print(f"⚠️ Failed to parse JSON from Gemini response")
                print(f"   First 200 chars: {response_text[:200]}")
            
            if not analysis_data:
                # Retry with cleaned response
                analysis_data = parse_json_safely(response_text)
                if not analysis_data:
                    return {
                        "error": "Failed to parse Gemini response",
                        "raw_response": response_text[:500]  # First 500 chars for debugging
                    }
            
            # Structure the analysis result
            result = {
                "sentiment": analysis_data.get("sentiment", "neutral"),
                "confidence_score": float(analysis_data.get("confidence_score", 0.5)),
                "emotions": analysis_data.get("emotions", []),
                "urgency": extract_urgency_level(analysis_data.get("urgency", {})),
                "urgency_reason": extract_urgency_reason(analysis_data.get("urgency", {})),
                "urgency_flags": extract_urgency_flags(analysis_data.get("urgency", {})),
                "primary_category": None,
                "subcategories": [],
                "medical_concerns": None,
                "actionable_insights": analysis_data.get("actionable_insights", ""),
                "key_points": analysis_data.get("key_points", [])
            }
            
            # Extract categories
            categories = extract_categories(analysis_data.get("categories", {}))
            result["primary_category"] = categories[0]
            result["subcategories"] = categories[1]
            
            # Extract medical concerns
            result["medical_concerns"] = extract_medical_concerns(
                analysis_data.get("medical_concerns", {})
            )
            
            return result
            
        except Exception as e:
            # Handle various errors
            error_message = str(e)
            
            # Rate limit handling
            if "429" in error_message or "rate limit" in error_message.lower():
                return {
                    "error": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                }
            
            # Connection errors
            if "connection" in error_message.lower() or "timeout" in error_message.lower():
                return {
                    "error": "Connection error. Please check your internet connection.",
                    "retry": True
                }
            
            # Generic error
            return {
                "error": f"Gemini API error: {error_message}",
                "retry": True
            }
    
    async def analyze_feedback_with_retry(
        self,
        feedback_text: str,
        department: str,
        doctor_name: Optional[str] = None,
        visit_date: Optional[str] = None,
        rating: Optional[int] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze feedback with retry logic
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        for attempt in range(max_retries):
            result = await self.analyze_feedback(
                feedback_text=feedback_text,
                department=department,
                doctor_name=doctor_name,
                visit_date=visit_date,
                rating=rating
            )
            
            # If no error, return result
            if "error" not in result:
                return result
            
            # If retry is not recommended, return error
            if not result.get("retry", False):
                return result
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)
        
        return result


# Global instance
gemini_service = GeminiService()

