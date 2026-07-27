"""
Dashboard service - business logic for dashboard analytics and statistics.

Provides:
- Aggregate platform statistics
- Doctor-specific dashboards
- Patient-specific dashboards
- Real-time consultation metrics
- Notification management
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from loguru import logger

from app.repositories.patient_repository import patient_repository
from app.repositories.consultation_repository import consultation_repository
from app.repositories.doctor_repository import doctor_repository
from app.repositories.appointment_repository import appointment_repository
from app.core.database import supabase


class DashboardService:
    """Service layer for dashboard and analytics operations."""

    def get_platform_stats(self) -> dict:
        """Get aggregate platform-wide statistics."""
        try:
            # Total patients
            patients = patient_repository.get_all()
            total_patients = len(patients)

            # Total consultations
            consultations = consultation_repository.get_all()
            total_consultations = len(consultations)
            active_consultations = len([
                c for c in consultations if c.get("status") == "active"
            ])
            completed_consultations = len([
                c for c in consultations if c.get("status") == "completed"
            ])

            # Total doctors
            doctors = doctor_repository.get_all()
            total_doctors = len(doctors)
            available_doctors = len([
                d for d in doctors if d.get("is_available", False)
            ])

            # Today's consultations
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            today_consultations = len([
                c for c in consultations
                if c.get("created_at", "") >= today_start
            ])

            # Average consultation duration (approximate)
            # Upcoming appointments
            upcoming = appointment_repository.get_upcoming(5)

            return {
                "total_patients": total_patients,
                "total_consultations": total_consultations,
                "active_consultations": active_consultations,
                "completed_consultations": completed_consultations,
                "today_consultations": today_consultations,
                "total_doctors": total_doctors,
                "available_doctors": available_doctors,
                "upcoming_appointments": len(upcoming),
            }

        except Exception as e:
            logger.error(f"Error fetching platform stats: {str(e)}")
            raise

    def get_recent_activity(self, limit: int = 10) -> list:
        """Get recent platform activity (latest consultations)."""
        try:
            consultations = consultation_repository.get_all()
            recent = sorted(
                consultations,
                key=lambda c: c.get("created_at", ""),
                reverse=True,
            )[:limit]

            activity = []
            for c in recent:
                try:
                    patient = patient_repository.get_by_id(c.get("patient_id", ""))
                    activity.append({
                        "id": c.get("id"),
                        "type": "consultation",
                        "status": c.get("status"),
                        "patient_name": patient.get("name", "Unknown"),
                        "timestamp": c.get("created_at"),
                    })
                except Exception:
                    activity.append({
                        "id": c.get("id"),
                        "type": "consultation",
                        "status": c.get("status"),
                        "patient_name": "Unknown",
                        "timestamp": c.get("created_at"),
                    })

            return activity
        except Exception as e:
            logger.error(f"Error fetching recent activity: {str(e)}")
            raise

    def get_consultation_trends(self, days: int = 7) -> dict:
        """Get consultation trends over a period."""
        try:
            consultations = consultation_repository.get_all()
            now = datetime.now(timezone.utc)

            daily_stats = {}
            for i in range(days - 1, -1, -1):
                day = now - timedelta(days=i)
                day_key = day.strftime("%Y-%m-%d")
                daily_stats[day_key] = {
                    "date": day_key,
                    "total": 0,
                    "active": 0,
                    "completed": 0,
                }

            for c in consultations:
                created = c.get("created_at", "")
                if created:
                    try:
                        c_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        day_key = c_date.strftime("%Y-%m-%d")
                        if day_key in daily_stats:
                            daily_stats[day_key]["total"] += 1
                            status = c.get("status")
                            if status == "active":
                                daily_stats[day_key]["active"] += 1
                            elif status == "completed":
                                daily_stats[day_key]["completed"] += 1
                    except (ValueError, AttributeError):
                        continue

            return {
                "trends": list(daily_stats.values()),
                "total_in_period": sum(s["total"] for s in daily_stats.values()),
            }

        except Exception as e:
            logger.error(f"Error fetching consultation trends: {str(e)}")
            raise

    def get_ai_usage_stats(self) -> dict:
        """Get AI service usage statistics."""
        try:
            # Count total AI messages from chat_messages table
            response = (
                supabase.table("chat_messages")
                .select("id", count="exact")
                .eq("sender", "assistant")
                .execute()
            )
            total_ai_messages = len(response.data) if response.data else 0

            # Count consultations with AI interactions
            consultations_with_ai = (
                supabase.table("consultations")
                .select("id", count="exact")
                .not_.eq("symptoms", None)
                .execute()
            )

            # Get total tokens used from ai_prompt_logs
            token_response = (
                supabase.table("ai_prompt_logs")
                .select("total_tokens")
                .execute()
            )
            total_tokens = sum(
                log.get("total_tokens", 0) for log in (token_response.data or [])
            )

            return {
                "total_ai_messages": total_ai_messages,
                "total_tokens_used": total_tokens,
                "consultations_with_ai": len(consultations_with_ai.data) if consultations_with_ai.data else 0,
            }

        except Exception as e:
            logger.error(f"Error fetching AI usage stats: {str(e)}")
            return {
                "total_ai_messages": 0,
                "total_tokens_used": 0,
                "consultations_with_ai": 0,
            }

    def get_notifications(self, user_id: str, limit: int = 20) -> list:
        """Get notifications for a specific user."""
        try:
            response = (
                supabase.table("notifications")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching notifications for {user_id}: {str(e)}")
            return []

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        try:
            supabase.table("notifications").update({
                "is_read": True
            }).eq("id", notification_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False

    def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        channel: str = "email",
        metadata: Optional[dict] = None,
    ) -> Optional[dict]:
        """Create a notification for a user."""
        try:
            response = (
                supabase.table("notifications")
                .insert({
                    "user_id": user_id,
                    "title": title,
                    "message": message,
                    "channel": channel,
                    "metadata": metadata or {},
                })
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return None

    def get_complete_dashboard(self) -> dict:
        """Get a complete dashboard with all stats."""
        stats = self.get_platform_stats()
        activity = self.get_recent_activity()
        trends = self.get_consultation_trends()
        ai_stats = self.get_ai_usage_stats()

        return {
            "stats": stats,
            "recent_activity": activity,
            "consultation_trends": trends,
            "ai_usage": ai_stats,
        }


# Singleton instance
dashboard_service = DashboardService()

