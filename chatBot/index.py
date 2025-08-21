from tool.LLM.index import (
        call_pwc_genai
    )
from chatBot.GetContext import (
    get_documents_by_date_range
)
import json


def create_analysis_prompt_template(json_context, user_prompt):
    prompt_template = f"""You are a SEBI regulatory compliance expert. Analyze the JSON context and provide a structured response to the user query.

CONTEXT:
{json_context}

QUERY: {user_prompt}

RESPONSE FORMAT:

##  EXECUTIVE SUMMARY
Brief overview of key regulatory changes and business impact.

##  DEPARTMENTAL IMPACT
For each affected department (Compliance, Risk, Trading, Finance, Customer Service):
**Changes:** Key regulatory updates
**Actions:** Specific tasks with timelines

##  ACTION TIMELINE
**Immediate (0-30 days):** Critical compliance items
**Short-term (1-3 months):** Implementation tasks  
**Long-term (3+ months):** Strategic initiatives

##  REGULATORY REFERENCES
List relevant SEBI circulars with:
- Title, Number, Date, URL, Key Impact

##  PRIORITY LEVELS
🔴 HIGH: Mandatory/deadline-driven
🟡 MEDIUM: Important improvements
🟢 LOW: Monitoring required

GUIDELINES:
- Use only provided JSON context
- State "Not specified" if data unavailable
- Include complete SEBI URLs
- Focus on actionable insights
- Prioritize by compliance deadlines

**CRITICAL: ALL relivenet (as per QUERY) regulatory references from the JSON context MUST be included. This is highly sensitive compliance data.**

**MANDATORY VERIFICATION CHECKLIST:**
✅ All relivenet (as per QUERY) documents from JSON context are listed
✅ No relivenet (as per QUERY) circular numbers are omitted
✅ All relivenet (as per QUERY) URLs are complete and accurate
✅ Every relivenet (as per QUERY) regulatory change is captured
✅ Cross-referenced with user query requirements

**Note:** If any regulatory reference exists in the context but is not explicitly mentioned in the user query, it MUST still be included if it's relevant to compliance requirements.


"""
    
    return prompt_template


async def chat_bot_response(prompt):
        
    try:
        # Get relevant documents based on time range
        get_context = get_documents_by_date_range(prompt)
        
        if "error" in get_context:
            return {
                "error": get_context["error"],
                "status": "failed"
            }
        
        # Convert to JSON string for the prompt
        context = json.dumps(get_context, indent=2)
        
        # Create the analysis prompt
        analysis_prompt = create_analysis_prompt_template(context, prompt)
        
        # Call the LLM with the structured prompt
        llm_response = await call_pwc_genai(
            model="vertex_ai.gemini-2.0-flash", 
            prompt=analysis_prompt
        )
        
        # Extract the result
        result = llm_response.get('choices', [{}])[0].get('text', '')
        
        return {
            "response": result,
            "metadata": {
                "total_documents_analyzed": get_context.get("metadata", {}).get("total_filtered_documents", 0),
                "date_range": get_context.get("metadata", {}).get("date_range", {}),
                "status": "success"
            }
        }
        
    except Exception as e:
        return {
            "error": f"Analysis failed: {str(e)}",
            "status": "failed"
        }


