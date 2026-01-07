"""
Web Filters service for handling business logic related to web filtering
"""
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path

from ...core.config import settings
from ...models.webfilters import (
    WebFilterProfile,
    WebFilterOverride,
    WebFilterLogEntry,
    WebFilterSearchRequest,
    WebFilterSearchResponse,
    WebFilterTestRequest,
    WebFilterTestResult,
    WebFilterBulkUpdateRequest,
    WebFilterBulkUpdateResponse,
    WebFilterStats,
    WebFilterAction
)

logger = logging.getLogger(__name__)

class WebFilterService:
    """Service for handling web filter operations"""
    
    def __init__(self):
        self.profiles: Dict[str, WebFilterProfile] = {}
        self.overrides: Dict[str, WebFilterOverride] = {}
        self.logs: List[WebFilterLogEntry] = []
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize with mock data for development"""
        # Mock profiles
        default_profile = WebFilterProfile(
            id="default",
            name="Default Profile",
            description="Default web filtering profile",
            categories=[
                {"id": 1, "name": "Malware", "type": "security"},
                {"id": 2, "name": "Phishing", "type": "security"},
                {"id": 3, "name": "Adult", "type": "content"},
                {"id": 4, "name": "Social Media", "type": "productivity"},
            ],
            default_action=WebFilterAction.BLOCK,
            log_all_url=True,
            block_page_mode="message"
        )
        self.profiles[default_profile.id] = default_profile
        
        # Mock overrides
        override = WebFilterOverride(
            id="override1",
            name="Marketing Team",
            description="Allow social media for marketing team",
            status="enabled",
            user_group="marketing",
            profile="default"
        )
        self.overrides[override.id] = override
        
        # Mock logs
        self._generate_mock_logs()
    
    def _generate_mock_logs(self, count: int = 100):
        """Generate mock log entries for testing"""
        import random
        from faker import Faker
        
        fake = Faker()
        actions = [a.value for a in WebFilterAction]
        categories = ["Social Media", "News", "Shopping", "Technology", "Entertainment", "Adult"]
        
        for i in range(count):
            timestamp = datetime.utcnow() - timedelta(minutes=random.randint(0, 10080))  # Up to 1 week old
            url = fake.uri()
            action = random.choice(actions)
            
            log_entry = WebFilterLogEntry(
                id=f"log_{i}",
                timestamp=timestamp,
                src_ip=fake.ipv4(),
                user=fake.user_name(),
                url=url,
                hostname=url.split("//")[-1].split("/")[0],
                path="/" + "/".join(url.split("//")[-1].split("/")[1:]),
                method=random.choice(["GET", "POST", "PUT", "DELETE"]),
                action=action,
                profile="default",
                category=random.choice(categories),
                reason="Policy match" if action == "block" else None,
                user_agent=fake.user_agent(),
                referrer=fake.uri() if random.random() > 0.7 else None,
                bytes_sent=random.randint(100, 100000),
                bytes_received=random.randint(100, 5000)
            )
            self.logs.append(log_entry)
    
    async def search_logs(
        self, 
        search_request: WebFilterSearchRequest
    ) -> WebFilterSearchResponse:
        """
        Search web filter logs based on the provided criteria
        """
        try:
            filtered_logs = self.logs.copy()
            
            # Apply filters
            if search_request.query:
                query = search_request.query.lower()
                filtered_logs = [
                    log for log in filtered_logs
                    if (query in log.url.lower() or 
                        (log.user and query in log.user.lower()) or
                        (log.hostname and query in log.hostname.lower()) or
                        (log.path and query in log.path.lower()) or
                        (log.referrer and query in log.referrer.lower()))
                ]
            
            if search_request.start_time:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.timestamp >= search_request.start_time
                ]
                
            if search_request.end_time:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.timestamp <= search_request.end_time
                ]
                
            if search_request.src_ip:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.src_ip == search_request.src_ip
                ]
                
            if search_request.user:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.user and log.user.lower() == search_request.user.lower()
                ]
                
            if search_request.action:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.action == search_request.action
                ]
                
            if search_request.category:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.category and search_request.category.lower() in log.category.lower()
                ]
                
            if search_request.profile:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.profile == search_request.profile
                ]
            
            # Apply pagination
            total = len(filtered_logs)
            paginated_logs = filtered_logs[
                search_request.offset:search_request.offset + search_request.limit
            ]
            
            return WebFilterSearchResponse(
                total=total,
                count=len(paginated_logs),
                offset=search_request.offset,
                limit=search_request.limit,
                results=paginated_logs
            )
            
        except Exception as e:
            logger.error(f"Error searching web filter logs: {str(e)}", exc_info=True)
            raise
    
    async def test_url(
        self, 
        test_request: WebFilterTestRequest
    ) -> WebFilterTestResult:
        """
        Test how a URL would be handled by the web filter
        """
        try:
            # In a real implementation, this would query the actual web filter
            # For now, we'll use a simple mock implementation
            
            # Check for overrides first
            override_match = None
            for override in self.overrides.values():
                if override.status != "enabled":
                    continue
                    
                # Simple matching logic - in reality, this would check IP ranges, user groups, etc.
                if (test_request.user and override.user and 
                    test_request.user.lower() == override.user.lower()):
                    override_match = override
                    break
                
                if (test_request.user_group and override.user_group and 
                    test_request.user_group.lower() == override.user_group.lower()):
                    override_match = override
                    break
            
            # Determine profile to use
            profile_id = test_request.profile or "default"
            profile = self.profiles.get(profile_id)
            
            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")
            
            # Simple categorization - in reality, this would query a URL categorization service
            categories = ["Social Media", "News", "Shopping", "Technology", "Entertainment", "Adult"]
            category = categories[hash(test_request.url) % len(categories)]
            
            # Simple action determination
            if category in ["Adult", "Gambling"]:
                action = WebFilterAction.BLOCK
                reason = f"Blocked category: {category}"
            elif category in ["Social Media", "Streaming"] and not override_match:
                action = WebFilterAction.BLOCK
                reason = f"Blocked category: {category}"
            else:
                action = WebFilterAction.ALLOW
                reason = "Allowed by policy"
            
            # If there's an override, use the override profile
            if override_match:
                override_profile = self.profiles.get(override_match.profile)
                if override_profile:
                    profile = override_profile
                    action = WebFilterAction.ALLOW
                    reason = "Allowed by override"
            
            return WebFilterTestResult(
                url=test_request.url,
                action=action,
                profile=profile.name,
                category=category,
                reason=reason,
                is_overridden=bool(override_match),
                override_details={
                    "id": override_match.id,
                    "name": override_match.name
                } if override_match else None
            )
            
        except Exception as e:
            logger.error(f"Error testing URL: {str(e)}", exc_info=True)
            raise
    
    async def bulk_update_urls(
        self, 
        update_request: WebFilterBulkUpdateRequest
    ) -> WebFilterBulkUpdateResponse:
        """
        Perform bulk updates to web filter URLs
        """
        try:
            # In a real implementation, this would update the actual web filter
            # For now, we'll just return a mock response
            
            success_count = 0
            errors = []
            
            for i, url in enumerate(update_request.urls):
                try:
                    # Simulate some failures for testing
                    if i % 10 == 0:  # Fail every 10th request
                        raise ValueError(f"Failed to update URL: {url}")
                        
                    # In a real implementation, we would update the web filter here
                    success_count += 1
                    
                except Exception as e:
                    errors.append({
                        "url": str(url),
                        "error": str(e)
                    })
            
            return WebFilterBulkUpdateResponse(
                total=len(update_request.urls),
                success=success_count,
                failed=len(errors),
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in bulk update: {str(e)}", exc_info=True)
            raise
    
    async def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        profile_id: Optional[str] = None
    ) -> WebFilterStats:
        """
        Get web filter statistics
        """
        try:
            # Filter logs by time range and profile
            filtered_logs = self.logs.copy()
            
            if start_time:
                filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
                
            if end_time:
                filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
                
            if profile_id:
                filtered_logs = [log for log in filtered_logs if log.profile == profile_id]
            
            # Calculate basic statistics
            total_requests = len(filtered_logs)
            blocked_requests = len([log for log in filtered_logs if log.action == WebFilterAction.BLOCK])
            allowed_requests = len([log for log in filtered_logs if log.action == WebFilterAction.ALLOW])
            monitored_requests = len([log for log in filtered_logs if log.action == WebFilterAction.MONITOR])
            
            # Calculate top categories
            from collections import Counter
            category_counts = Counter(log.category for log in filtered_logs if log.category)
            top_categories = [
                {"category": cat, "count": count, "percentage": (count / total_requests) * 100 if total_requests > 0 else 0}
                for cat, count in category_counts.most_common(10)
            ]
            
            # Calculate top blocked domains
            blocked_domains = Counter(
                log.hostname for log in filtered_logs 
                if log.action == WebFilterAction.BLOCK and log.hostname
            )
            top_blocked_domains = [
                {"domain": domain, "count": count}
                for domain, count in blocked_domains.most_common(10)
            ]
            
            # Calculate top users
            user_requests = Counter(
                log.user for log in filtered_logs 
                if log.user
            )
            top_users = [
                {"user": user, "count": count}
                for user, count in user_requests.most_common(10)
            ]
            
            # Generate time series data (hourly buckets)
            time_series = []
            if filtered_logs:
                min_time = min(log.timestamp for log in filtered_logs)
                max_time = max(log.timestamp for log in filtered_logs)
                
                # Create hourly buckets
                current_time = min_time.replace(minute=0, second=0, microsecond=0)
                while current_time <= max_time:
                    next_time = current_time + timedelta(hours=1)
                    
                    # Count requests in this hour
                    hour_logs = [
                        log for log in filtered_logs
                        if current_time <= log.timestamp < next_time
                    ]
                    
                    time_series.append({
                        "time": current_time.isoformat(),
                        "total": len(hour_logs),
                        "blocked": len([log for log in hour_logs if log.action == WebFilterAction.BLOCK]),
                        "allowed": len([log for log in hour_logs if log.action == WebFilterAction.ALLOW]),
                    })
                    
                    current_time = next_time
            
            return WebFilterStats(
                total_requests=total_requests,
                blocked_requests=blocked_requests,
                allowed_requests=allowed_requests,
                monitored_requests=monitored_requests,
                top_categories=top_categories,
                top_blocked_domains=top_blocked_domains,
                top_users=top_users,
                time_series=time_series,
                time_range={
                    "start": start_time or (min(log.timestamp for log in self.logs) if self.logs else datetime.utcnow()),
                    "end": end_time or datetime.utcnow()
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
            raise

# Create a singleton instance of the service
webfilter_service = WebFilterService()
