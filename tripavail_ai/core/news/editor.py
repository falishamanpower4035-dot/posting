#!/usr/bin/env python3
"""
TripAvail AI Tourism Editor
Intelligent analysis of tourism-related news articles
"""

import os
import json
import openai
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TourismEditor:
    """Intelligent tourism editor that analyzes news articles for travel relevance"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")
        self.raw_news_file = self.data_dir / "raw_news.json"
        self.processed_news_file = self.data_dir / "processed_news.json"
        self.editor_log_file = self.logs_dir / "tourism_editor.log"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Note: Logging configured centrally via core.utils.logging_setup
        # Logs will flow to app.log with automatic rotation
        
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    def load_news_articles(self) -> Optional[List[Dict]]:
        """Load news articles from raw_news.json"""
        if not self.raw_news_file.exists():
            logger.warning("No raw news file found")
            return None
        
        try:
            with open(self.raw_news_file, 'r') as f:
                data = json.load(f)
                articles = data.get('articles', [])
                
                # CRITICAL: Filter out already-used news articles BEFORE analysis
                # This prevents duplicate posts at the source and saves OpenAI costs
                from core.content.post_manager import PostManager
                pm = PostManager()
                
                unused_articles = []
                skipped_count = 0
                for article in articles:
                    if not pm.is_news_already_used(article):
                        unused_articles.append(article)
                    else:
                        skipped_count += 1
                        title = article.get('title', 'Unknown')[:60]
                        url = article.get('link', article.get('url', 'N/A'))
                        logger.info(f"⚠️ Skipping already-used article: {title} ({url})")
                
                if skipped_count > 0:
                    logger.info(f"Filtered out {skipped_count} already-used articles before analysis")
                
                logger.info(f"Loaded {len(unused_articles)} unused articles for analysis (filtered from {len(articles)} total)")
                return unused_articles
        except Exception as e:
            logger.error(f"Failed to load news articles: {e}")
            return None
    
    def create_analysis_prompt(self, articles: List[Dict]) -> str:
        """Create a prompt for OpenAI to analyze tourism relevance"""
        
        # Format articles for the prompt (batch of 20 articles)
        # OPTIMIZATION: Truncate descriptions to 250 chars to reduce token usage while keeping context
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'N/A')
            description = article.get('description', 'N/A')
            
            # Truncate description to first 250 characters to save tokens
            # Title + first 250 chars is sufficient for tourism relevance analysis
            if len(description) > 250:
                description = description[:250] + "..."
            
            articles_text += f"""
Article {i}:
Title: {title}
Description: {description}
Country: {', '.join(article.get('country', []))}
Category: {', '.join(article.get('category', []))}
Published: {article.get('pubDate', 'N/A')}
Source: {article.get('source_id', 'N/A')}
Link: {article.get('link', 'N/A')}
---
"""
        
        prompt = f"""You are TripAvail's Global Tourism News Selector.

Your role is to filter and rank the top 3-5 tourism stories from a batch of 20 articles for global travel and tourism audiences.

GLOBAL TOURISM NEWS SELECTOR PROMPT PACK:

CRITERIA FOR SELECTION:
1. Tourism Relevance: Focus ONLY on tourism, destinations, travel policies, airlines, hospitality, eco-tourism, sustainability, events, culture, and visas.
2. Global Impact: Stories that affect international travelers or showcase global destinations.
3. Travel Inspiration: Articles that inspire travel, highlight new attractions, or showcase unique experiences.
4. Policy Updates: Visa changes, entry requirements, or travel regulations that impact tourists.
5. Industry News: Airlines, hotels, hospitality trends, and tourism industry developments.
6. Cultural Tourism: Events, festivals, cultural sites, and heritage attractions.
7. Sustainable Travel: Eco-tourism, environmental initiatives, and responsible travel practices.

FILTERING RULES:
- Ignore politics, generic finance, war, sports, or non-tourism topics unless directly impacting travel
- Prioritize positive or informative angles over negative events
- Ensure global representation across continents (Asia, Europe, Americas, Africa, Oceania, Middle East)
- Focus on actionable information for travelers

RANKING SYSTEM:
- Score 8-10: Highly relevant, actionable tourism information
- Score 6-7: Moderately relevant, interesting for travelers
- Score 4-5: Somewhat relevant, niche tourism interest
- Score 0-3: Not relevant for tourism audiences

SELECTION CRITERIA:
- ONLY select stories with scores 7-10 (above 6)
- Reject any stories with scores 6 or below
- Prioritize higher scores (8-10) over lower scores (7)

OUTPUT REQUIREMENTS:
Return only stories with scores above 6, ranked by relevance and impact.

CRITICAL: Return ONLY valid JSON array. Do not include any explanatory text, comments, or additional text before or after the JSON.

Output JSON strictly in this format (NO OTHER TEXT):
[
  {{
    "title": "...",
    "summary": "...",
    "reason": "...",
    "region": "...",
    "score": 0-10,
    "source": "NewsData.io"
  }}
]

Articles to analyze (Batch of {len(articles)} articles):
{articles_text}

IMPORTANT: Return ONLY the JSON array. No explanations, no comments, no additional text. Start your response with [ and end with ]."""
        
        return prompt
    
    def analyze_articles_with_openai(self, articles: List[Dict]) -> Optional[List[Dict]]:
        """Use OpenAI to analyze articles for tourism relevance"""
        try:
            prompt = self.create_analysis_prompt(articles)
            
            logger.info("Sending articles to OpenAI for tourism analysis...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are TripAvail's Global Tourism News Selector. You are an expert at filtering and ranking tourism-relevant news from global sources. You excel at identifying the top 3-5 most important tourism stories from batches of articles, focusing on actionable information for travelers worldwide."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Extract JSON from response (handle structured / missing content)
            message = response.choices[0].message
            content = getattr(message, "content", None)

            if isinstance(content, list):
                parts: List[str] = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append(part.get("text", ""))
                    else:
                        parts.append(str(part))
                content = "\n".join(parts).strip()
            elif isinstance(content, str):
                content = content.strip()
            elif content is None:
                logger.error("OpenAI returned empty content for tourism analysis response")
                try:
                    raw_dump = response.model_dump()
                except Exception:
                    raw_dump = str(response)
                logger.debug(f"Raw OpenAI response (empty content): {raw_dump}")
                return None
            else:
                content = str(content).strip()
            
            # Try to extract JSON from the response
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # CRITICAL: Robust JSON extraction that handles explanatory text
            # OpenAI sometimes returns: "Based on articles...\n\n[{...}]\n\nRemaining articles..."
            # Strategy: Find the largest valid JSON array by trying different extraction methods
            analyzed_articles = None
            
            # Method 1: Try direct parsing (fastest path)
            try:
                analyzed_articles = json.loads(content)
                logger.debug("Direct JSON parsing succeeded")
            except json.JSONDecodeError:
                # Method 2: Extract JSON array using regex (greedy match from first [ to last ])
                import re
                json_array_match = re.search(r'(\[[\s\S]*\])', content)
                if json_array_match:
                    try:
                        extracted = json_array_match.group(1)
                        analyzed_articles = json.loads(extracted)
                        logger.debug("Extracted JSON array from response with explanatory text")
                    except json.JSONDecodeError:
                        # Method 3: Find valid JSON by scanning from different positions
                        # Look for the opening bracket and try to parse progressively
                        bracket_pos = content.find('[')
                        if bracket_pos >= 0:
                            # Try parsing from the bracket position onwards
                            for end_pos in range(len(content), bracket_pos, -1):
                                try:
                                    candidate = content[bracket_pos:end_pos].strip()
                                    analyzed_articles = json.loads(candidate)
                                    logger.debug(f"Found valid JSON by scanning from position {bracket_pos}")
                                    break
                                except json.JSONDecodeError:
                                    continue
            
            # Final validation
            if analyzed_articles is None:
                logger.error(f"Failed to extract valid JSON from OpenAI response")
                logger.debug(f"Raw response preview: {content[:500]}...")
                return None
            
            # Ensure it's a list
            if not isinstance(analyzed_articles, list):
                logger.error(f"Expected JSON array, got {type(analyzed_articles)}")
                return None
            
            try:
                logger.info(f"Successfully analyzed {len(analyzed_articles)} tourism-relevant articles")
                
                # CRITICAL: Map analyzed articles back to original articles to preserve 'link' field
                # This is essential for duplicate detection
                # Use multiple matching strategies to ensure we find the original article
                for analyzed in analyzed_articles:
                    analyzed_title = analyzed.get('title', '').strip()
                    matched = False
                    
                    # Strategy 1: Try exact title match (fastest)
                    for original in articles:
                        if original.get('title', '').strip() == analyzed_title:
                            # Preserve link and other original metadata
                            analyzed['link'] = original.get('link', '')
                            analyzed['article_id'] = original.get('article_id', '')
                            analyzed['pubDate'] = original.get('pubDate', '')
                            matched = True
                            break
                    
                    # Strategy 2: If exact match failed, try normalized title match (case-insensitive)
                    if not matched:
                        analyzed_normalized = ' '.join(analyzed_title.lower().split())
                        for original in articles:
                            original_title = original.get('title', '').strip()
                            original_normalized = ' '.join(original_title.lower().split())
                            if original_normalized == analyzed_normalized:
                                analyzed['link'] = original.get('link', '')
                                analyzed['article_id'] = original.get('article_id', '')
                                analyzed['pubDate'] = original.get('pubDate', '')
                                matched = True
                                logger.warning(f"Title match required normalization: '{analyzed_title}' -> '{original_title}'")
                                break
                    
                    # Strategy 3: If still not matched, try fuzzy match (first 50 chars, case-insensitive)
                    if not matched:
                        analyzed_prefix = analyzed_title[:50].lower().strip()
                        for original in articles:
                            original_title = original.get('title', '').strip()
                            original_prefix = original_title[:50].lower().strip()
                            if original_prefix == analyzed_prefix:
                                analyzed['link'] = original.get('link', '')
                                analyzed['article_id'] = original.get('article_id', '')
                                analyzed['pubDate'] = original.get('pubDate', '')
                                matched = True
                                logger.warning(f"Title match required prefix matching: '{analyzed_title}' -> '{original_title}'")
                                break
                    
                    # Strategy 4: If still no match, log warning but try to preserve by checking if link exists in original
                    if not matched:
                        logger.warning(f"⚠️ Could not map analyzed article to original: '{analyzed_title}'")
                        logger.warning(f"   Link field may be missing - duplicate detection may fail!")
                        # At least try to preserve any existing link in analyzed article
                        if 'link' not in analyzed:
                            analyzed['link'] = ''
                
                return analyzed_articles
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.debug(f"Raw response: {content}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return None
    
    def save_processed_news(self, analyzed_articles: List[Dict], original_timestamp: str, total_analyzed: int):
        """Save the processed tourism-relevant articles"""
        try:
            from datetime import datetime, timezone
            
            processed_data = {
                "timestamp": original_timestamp,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "source": "TripAvail AI Global Tourism News Selector",
                "input_source": "NewsData.io",
                "batch_size": total_analyzed,
                "top_stories_count": len(analyzed_articles),
                "top_tourism_stories": analyzed_articles
            }
            
            with open(self.processed_news_file, 'w') as f:
                json.dump(processed_data, f, indent=2)
            
            logger.info(f"Saved {len(analyzed_articles)} top tourism stories to {self.processed_news_file}")
            
        except Exception as e:
            logger.error(f"Failed to save processed news: {e}")
    
    def log_editor_activity(self, total_articles: int, relevant_articles: int):
        """Log the editor's activity"""
        try:
            log_entry = f"Tourism Editor Analysis: {total_articles} articles analyzed, {relevant_articles} tourism-relevant articles identified\n"
            with open(self.editor_log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to log editor activity: {e}")
    
    def run_analysis(self):
        """Run the complete tourism analysis process"""
        logger.info("Starting TripAvail Tourism Editor analysis...")
        
        # Load articles (already filtered for duplicates at source)
        articles = self.load_news_articles()
        if not articles:
            logger.warning("No unused articles to analyze")
            return
        
        # If no articles after filtering, skip analysis to save OpenAI costs
        if len(articles) == 0:
            logger.info("All articles already used - skipping OpenAI analysis to save costs")
            return
        
        # Get original timestamp
        try:
            with open(self.raw_news_file, 'r') as f:
                raw_data = json.load(f)
                original_timestamp = raw_data.get('timestamp', 'unknown')
        except:
            original_timestamp = 'unknown'
        
        # Analyze with OpenAI (only unused articles)
        analyzed_articles = self.analyze_articles_with_openai(articles)
        if not analyzed_articles:
            logger.error("Analysis failed")
            return
        
        # Save results
        self.save_processed_news(analyzed_articles, original_timestamp, len(articles))
        
        # Log activity
        self.log_editor_activity(len(articles), len(analyzed_articles))
        
        # Display results
        logger.info("Global Tourism News Selector Analysis Complete!")
        logger.info(f"Analyzed batch of {len(articles)} unused articles from NewsData.io")
        logger.info(f"Selected top {len(analyzed_articles)} tourism stories:")
        
        for i, article in enumerate(analyzed_articles, 1):
            logger.info(f"{i}. {article.get('title', 'N/A')} (Score: {article.get('score', 'N/A')}) - {article.get('region', 'N/A')}")
        
        return analyzed_articles
    
    def get_latest_analysis(self) -> Optional[List[Dict]]:
        """Get the latest tourism analysis results"""
        if not self.processed_news_file.exists():
            return None
        
        try:
            with open(self.processed_news_file, 'r') as f:
                data = json.load(f)
                return data.get('top_tourism_stories', [])
        except Exception as e:
            logger.error(f"Failed to load latest analysis: {e}")
            return None

def main():
    """Main function for testing"""
    try:
        editor = TourismEditor()
        results = editor.run_analysis()
        
        if results:
            print("\nTop Tourism Stories Analysis Results:")
            print("=" * 50)
            for i, article in enumerate(results, 1):
                print(f"\n{i}. {article.get('title', 'N/A')}")
                print(f"   Region: {article.get('region', 'N/A')}")
                print(f"   Score: {article.get('score', 'N/A')}/10")
                print(f"   Source: {article.get('source', 'N/A')}")
                print(f"   Summary: {article.get('summary', 'N/A')}")
                print(f"   Reason: {article.get('reason', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
