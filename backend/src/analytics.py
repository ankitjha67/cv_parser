from typing import List, Dict
from src.schemas import MatchReport, CompetitiveAnalysis, IndustryBenchmark
import statistics

def calculate_competitive_analysis(
    user_report: MatchReport,
    all_reports: List[MatchReport]
) -> CompetitiveAnalysis:
    """
    Calculate how user's CV ranks against aggregate data.
    """
    if not all_reports:
        return CompetitiveAnalysis(
            user_score=user_report.total_score,
            percentile_rank=100.0,
            better_than_percent=100.0,
            industry_avg=user_report.total_score,
            gap_to_top_10=0.0,
            strengths=[],
            improvement_areas=[]
        )
    
    scores = [r.total_score for r in all_reports]
    scores.sort()
    
    # Calculate percentile
    user_score = user_report.total_score
    lower_count = sum(1 for s in scores if s < user_score)
    percentile = (lower_count / len(scores)) * 100
    
    # Industry averages
    industry_avg = statistics.mean(scores)
    top_10_threshold = statistics.quantiles(scores, n=10)[8] if len(scores) >= 10 else max(scores)
    
    # Identify strengths (categories above average)
    strengths = []
    improvement_areas = []
    
    for category, score in user_report.category_scores.items():
        # Calculate average for this category across all reports
        category_scores = [r.category_scores.get(category, 0) for r in all_reports if category in r.category_scores]
        if category_scores:
            avg_category = statistics.mean(category_scores)
            if score > avg_category:
                strengths.append(f"{category.capitalize()}: {score:.1f} (avg: {avg_category:.1f})")
            elif score < avg_category * 0.8:  # 20% below average
                improvement_areas.append(f"{category.capitalize()}: {score:.1f} (avg: {avg_category:.1f})")
    
    return CompetitiveAnalysis(
        user_score=user_score,
        percentile_rank=percentile,
        better_than_percent=percentile,
        industry_avg=industry_avg,
        gap_to_top_10=max(0, top_10_threshold - user_score),
        strengths=strengths[:5],  # Top 5
        improvement_areas=improvement_areas[:5]
    )

def calculate_industry_benchmarks(all_reports: List[MatchReport]) -> IndustryBenchmark:
    """
    Calculate industry-wide benchmark statistics.
    """
    if not all_reports:
        return IndustryBenchmark(
            industry="General",
            avg_score=0.0,
            top_10_percentile=0.0,
            top_25_percentile=0.0,
            median_score=0.0,
            sample_size=0
        )
    
    scores = [r.total_score for r in all_reports]
    scores.sort()
    
    return IndustryBenchmark(
        industry="Software Engineering",  # Can be dynamic based on JD
        avg_score=statistics.mean(scores),
        top_10_percentile=statistics.quantiles(scores, n=10)[8] if len(scores) >= 10 else max(scores),
        top_25_percentile=statistics.quantiles(scores, n=4)[2] if len(scores) >= 4 else max(scores),
        median_score=statistics.median(scores),
        sample_size=len(scores)
    )

def calculate_success_rate_by_score_threshold(
    applications: List[Dict],
    threshold_ranges: List[tuple] = [(0, 40), (40, 60), (60, 80), (80, 100)]
) -> Dict[str, Dict]:
    """
    Calculate success rates (offer/accept) by score ranges.
    """
    results = {}
    
    for min_score, max_score in threshold_ranges:
        range_key = f"{min_score}-{max_score}"
        apps_in_range = [
            app for app in applications 
            if app.get('match_score') and min_score <= app['match_score'] < max_score
        ]
        
        if not apps_in_range:
            results[range_key] = {
                'total': 0,
                'offers': 0,
                'success_rate': 0.0,
                'avg_score': 0.0
            }
            continue
        
        offers = sum(1 for app in apps_in_range if app.get('status') in ['offer', 'accepted'])
        
        results[range_key] = {
            'total': len(apps_in_range),
            'offers': offers,
            'success_rate': (offers / len(apps_in_range)) * 100 if apps_in_range else 0.0,
            'avg_score': statistics.mean([app['match_score'] for app in apps_in_range])
        }
    
    return results
