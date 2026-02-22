import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import Counter
from neo4j import GraphDatabase
import config
import pandas as pd

# ── Issue-type normalisation map ──────────────────────────────────────
# Maps lowercased, underscore-stripped issue types → canonical label.
# Any value not in this map is title-cased automatically.
_ISSUE_SYNONYMS = {
    "delivery delay": "Delivery Delay",
    "delivery_delay": "Delivery Delay",
    "late delivery": "Delivery Delay",
    "delayed delivery": "Delivery Delay",
    "delay": "Delivery Delay",
    "order delay": "Delivery Delay",
    "service delay": "Delivery Delay",
    "delivery delay and lack of updates": "Delivery & Communication Delay",
    "delivery delays and lack of communication": "Delivery & Communication Delay",
    "delivery performance": "Delivery Performance",
    "delivery_feedback": "Delivery Feedback",
    "missing delivery confirmation": "Delivery Confirmation Issue",
    "cancellation confirmation": "Order Cancellation",
    "order cancellation": "Order Cancellation",
    "order status inconsistency": "Order Status Issue",
    "resource_request": "Resource Request",
    "capacity planning": "Capacity Planning",
    "system downtime": "System Downtime",
    "unusual order pattern": "Unusual Order Pattern",
    "high demand": "High Demand",
    "traffic": "High Demand",
    "service quality": "Service Quality",
    "data quality": "Data Quality",
    "food quality": "Food Quality",
    "feedback": "Feedback",
    "positive feedback": "Positive Feedback",
    "support appreciation": "Support Appreciation",
    "refund appreciation": "Refund Appreciation",
    "service recovery": "Service Recovery",
    "fraud": "Fraud",
    "performance": "Performance",
}


def normalize_issue_type(raw: str) -> str:
    """Return a canonical issue-type label.

    1. Strip whitespace, lowercase, replace underscores with spaces.
    2. Look up in the synonym map.
    3. Fall back to title-cased version of the cleaned string.
    """
    if not raw:
        return "Unknown"
    key = raw.strip().lower().replace("_", " ")
    return _ISSUE_SYNONYMS.get(key, key.title())


class KPICalculator:
    """Calculate KPIs for enterprise intelligence"""
    
    def __init__(self):
        """Initialize KPI calculator with Neo4j connection"""
        self.driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        self.output_dir = config.OUTPUT_DIR
        self.kpis = {}
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def calculate_all_kpis(self) -> Dict[str, Any]:
        """Calculate all KPIs"""
        print("\n📊 Calculating KPIs...")
        
        self.kpis = {
            "data_quality": self._calculate_data_quality(),
            "issue_analytics": self._calculate_issue_analytics(),
            "sentiment_analysis": self._calculate_sentiment_analysis(),
            "agent_performance": self._calculate_agent_performance(),
            "customer_metrics": self._calculate_customer_metrics(),
            "graph_metrics": self._calculate_graph_metrics(),
            "timestamp": datetime.now().isoformat()
        }
        
        return self.kpis
    
    def _calculate_data_quality(self) -> Dict:
        """Calculate data quality KPIs"""
        try:
            total_files = 0
            valid_files = 0
            missing_fields = 0
            total_records = 0
            
            # Check email outputs
            for file in os.listdir(self.output_dir):
                if file.startswith("email_") and file.endswith(".json"):
                    total_files += 1
                    try:
                        with open(os.path.join(self.output_dir, file), 'r') as f:
                            data = json.load(f)
                            total_records += 1
                            valid_files += 1
                            
                            # Count missing fields
                            required_fields = ["customer_id", "order_id", "issue_type", "sentiment"]
                            for field in required_fields:
                                if not data.get(field):
                                    missing_fields += 1
                    except:
                        pass
            
            # Check database NER file
            db_file = os.path.join(self.output_dir, "database_ner_flat.json")
            if os.path.exists(db_file):
                total_files += 1
                try:
                    with open(db_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            total_records += len(data)
                            valid_files += 1
                except:
                    pass
            
            return {
                "total_files": total_files,
                "valid_files": valid_files,
                "validity_rate": f"{(valid_files/total_files*100):.1f}%" if total_files > 0 else "0%",
                "total_records": total_records,
                "missing_fields_count": missing_fields,
                "data_completeness": f"{((total_records - missing_fields/4) / max(total_records, 1) * 100):.1f}%"
            }
        
        except Exception as e:
            print(f"❌ Error calculating data quality: {e}")
            return {"error": str(e)}
    
    def _calculate_issue_analytics(self) -> Dict:
        """Calculate issue-related KPIs"""
        try:
            issue_types = []
            issue_severities = []
            
            for file in os.listdir(self.output_dir):
                if file.startswith("email_") and file.endswith(".json"):
                    try:
                        with open(os.path.join(self.output_dir, file), 'r') as f:
                            data = json.load(f)
                            if data.get("issue_type"):
                                issue_types.append(normalize_issue_type(data["issue_type"]))
                            if data.get("severity"):
                                issue_severities.append(data.get("severity"))
                    except:
                        pass
            
            issue_distribution = dict(Counter(issue_types))
            top_issues = sorted(issue_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
            
            critical_count = sum(1 for s in issue_severities if str(s).strip().lower() in ["critical", "high"])
            
            return {
                "total_issues": len(issue_types),
                "unique_issue_types": len(issue_distribution),
                "top_5_issues": [{"type": t, "count": c} for t, c in top_issues],
                "issue_distribution": issue_distribution,
                "critical_issues": critical_count,
                "critical_rate": f"{(critical_count/max(len(issue_severities), 1)*100):.1f}%"
            }
        
        except Exception as e:
            print(f"❌ Error calculating issue analytics: {e}")
            return {"error": str(e)}
    
    def _calculate_sentiment_analysis(self) -> Dict:
        """Calculate sentiment-related KPIs"""
        try:
            sentiments = []
            sentiment_issues = {}  # issue_type -> sentiments
            
            for file in os.listdir(self.output_dir):
                if file.startswith("email_") and file.endswith(".json"):
                    try:
                        with open(os.path.join(self.output_dir, file), 'r') as f:
                            data = json.load(f)
                            sentiment = (data.get("sentiment") or "Neutral").strip().capitalize()
                            # Normalize common variants
                            if sentiment.lower() in ("concern", "concerned"):
                                sentiment = "Negative"
                            elif sentiment.lower() == "mixed":
                                sentiment = "Neutral"
                            sentiments.append(sentiment)
                            
                            issue = normalize_issue_type(data.get("issue_type", ""))
                            if issue not in sentiment_issues:
                                sentiment_issues[issue] = []
                            sentiment_issues[issue].append(sentiment)
                    except:
                        pass
            
            # Normalize sentiments to title case for consistent counting
            sentiment_dist_raw = dict(Counter(sentiments))
            sentiment_dist = {}
            for key, count in sentiment_dist_raw.items():
                normalized = key.strip().capitalize()
                # Group 'concern'/'concerned' into Negative
                if normalized in ("Concern", "Concerned"):
                    normalized = "Negative"
                sentiment_dist[normalized] = sentiment_dist.get(normalized, 0) + count
            
            positive = sentiment_dist.get("Positive", 0)
            negative = sentiment_dist.get("Negative", 0)
            neutral = sentiment_dist.get("Neutral", 0)
            # Also count 'Mixed' as neutral
            mixed = sentiment_dist.get("Mixed", 0)
            neutral += mixed
            total = len(sentiments)
            
            # Build sentiment breakdown per issue type (normalized)
            sentiment_by_issue = {}
            for issue, sents in sentiment_issues.items():
                breakdown = {}
                for s in sents:
                    norm = s.strip().capitalize()
                    if norm in ("Concern", "Concerned"):
                        norm = "Negative"
                    breakdown[norm] = breakdown.get(norm, 0) + 1
                sentiment_by_issue[issue] = breakdown

            return {
                "total_sentiments": total,
                "positive_count": positive,
                "positive_rate": f"{(positive/max(total, 1)*100):.1f}%",
                "negative_count": negative,
                "negative_rate": f"{(negative/max(total, 1)*100):.1f}%",
                "neutral_count": neutral,
                "neutral_rate": f"{(neutral/max(total, 1)*100):.1f}%",
                "sentiment_distribution": sentiment_dist,
                "sentiment_by_issue": sentiment_by_issue,
                "customer_satisfaction_score": f"{(positive/max(total, 1)*100):.1f}%"
            }
        
        except Exception as e:
            print(f"❌ Error calculating sentiment analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_agent_performance(self) -> Dict:
        """Calculate agent performance KPIs"""
        try:
            agent_issues = {}
            agent_sentiments = {}
            
            for file in os.listdir(self.output_dir):
                if file.startswith("email_") and file.endswith(".json"):
                    try:
                        with open(os.path.join(self.output_dir, file), 'r') as f:
                            data = json.load(f)
                            agent_id = data.get("agent_id") or "Unassigned"
                            
                            if agent_id not in agent_issues:
                                agent_issues[agent_id] = 0
                                agent_sentiments[agent_id] = []
                            
                            agent_issues[agent_id] += 1
                            agent_sentiments[agent_id].append(data.get("sentiment", "Neutral"))
                    except:
                        pass
            
            agent_metrics = []
            for agent, count in agent_issues.items():
                positive = sum(1 for s in agent_sentiments.get(agent, []) if str(s).lower() == "positive")
                satisfaction = (positive / max(count, 1)) * 100
                
                agent_metrics.append({
                    "agent_id": agent,
                    "issues_handled": count,
                    "positive_feedback": positive,
                    "satisfaction_score": f"{satisfaction:.1f}%"
                })
            
            agent_metrics = sorted(agent_metrics, key=lambda x: x["issues_handled"], reverse=True)
            
            return {
                "total_agents": len(agent_issues),
                "agents_with_unassigned": "Unassigned" in agent_issues,
                "average_issues_per_agent": f"{(sum(agent_issues.values())/max(len(agent_issues), 1)):.1f}",
                "top_agents": agent_metrics[:5],
                "all_agents": agent_metrics
            }
        
        except Exception as e:
            print(f"❌ Error calculating agent performance: {e}")
            return {"error": str(e)}
    
    def _calculate_customer_metrics(self) -> Dict:
        """Calculate customer-related KPIs"""
        try:
            customers = set()
            customer_orders = {}
            customer_sentiments = {}
            
            for file in os.listdir(self.output_dir):
                if file.startswith("email_") and file.endswith(".json"):
                    try:
                        with open(os.path.join(self.output_dir, file), 'r') as f:
                            data = json.load(f)
                            customer_id = data.get("customer_id", "Unknown")
                            order_id = data.get("order_id", "Unknown")
                            
                            if customer_id:
                                customers.add(customer_id)
                            
                            if customer_id not in customer_orders:
                                customer_orders[customer_id] = set()
                                customer_sentiments[customer_id] = []
                            
                            if order_id:
                                customer_orders[customer_id].add(order_id)
                            
                            customer_sentiments[customer_id].append(data.get("sentiment", "Neutral"))
                    except:
                        pass
            
            high_satisfaction_customers = sum(1 for cust, sentiments in customer_sentiments.items()
                                             if (sum(1 for s in sentiments if str(s).strip().lower() == "positive") / max(len(sentiments), 1)) > 0.5)
            
            # Count unique orders across all customers
            all_orders = set()
            for orders_set in customer_orders.values():
                if isinstance(orders_set, set):
                    all_orders.update(orders_set)
            
            return {
                "unique_customers": len(customers),
                "unique_orders": len(all_orders),
                "avg_orders_per_customer": f"{(sum(len(o) for o in customer_orders.values())/max(len(customer_orders), 1)):.1f}",
                "high_satisfaction_customers": high_satisfaction_customers,
                "high_satisfaction_rate": f"{(high_satisfaction_customers/max(len(customer_sentiments), 1)*100):.1f}%"
            }
        
        except Exception as e:
            print(f"❌ Error calculating customer metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_graph_metrics(self) -> Dict:
        """Calculate Neo4j graph metrics"""
        try:
            with self.driver.session() as session:
                # Count nodes by label
                node_counts = session.run(
                    "MATCH (n) RETURN labels(n)[0] as label, count(*) as count"
                ).data() or []
                
                # Count relationships
                relationship_counts = session.run(
                    "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count"
                ).data() or []
                
                return {
                    "message": "Graph metrics would require specific Neo4j queries",
                    "note": "Configure based on your Neo4j schema"
                }
        
        except Exception as e:
            print(f"⚠️  Neo4j connection issue (optional): {e}")
            return {"status": "Neo4j not currently available"}
    
    def export_kpis_to_json(self, filename: str = "kpi_report.json"):
        """Export KPIs to JSON file"""
        try:
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(self.kpis, f, indent=2)
            print(f"✅ KPI report saved to: {filepath}")
            return filepath
        
        except Exception as e:
            print(f"❌ Error exporting KPIs: {e}")
            return None
    
    def export_kpis_to_dataframe(self) -> pd.DataFrame:
        """Export KPIs to pandas DataFrame for analysis"""
        try:
            df_data = []
            
            for category, metrics in self.kpis.items():
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        df_data.append({
                            "Category": category,
                            "Metric": key,
                            "Value": str(value)
                        })
            
            return pd.DataFrame(df_data)
        
        except Exception as e:
            print(f"❌ Error exporting to DataFrame: {e}")
            return pd.DataFrame()
    
    def get_kpi_summary(self) -> Dict:
        """Get a quick summary of key KPIs"""
        return {
            "data_quality": self.kpis.get("data_quality", {}).get("data_completeness", "N/A"),
            "customer_satisfaction": self.kpis.get("sentiment_analysis", {}).get("customer_satisfaction_score", "N/A"),
            "total_issues": self.kpis.get("issue_analytics", {}).get("total_issues", 0),
            "critical_issues": self.kpis.get("issue_analytics", {}).get("critical_issues", 0),
            "unique_customers": self.kpis.get("customer_metrics", {}).get("unique_customers", 0),
            "top_agent": self.kpis.get("agent_performance", {}).get("top_agents", [{}])[0] if self.kpis.get("agent_performance", {}).get("top_agents") else {}
        }


# Test function
if __name__ == "__main__":
    kpi_calc = KPICalculator()
    kpis = kpi_calc.calculate_all_kpis()
    
    print("\n📊 KPI Summary:")
    print(json.dumps(kpi_calc.get_kpi_summary(), indent=2))
    
    kpi_calc.export_kpis_to_json()
    kpi_calc.close()
