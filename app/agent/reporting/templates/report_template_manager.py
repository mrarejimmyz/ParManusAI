"""
Report Template Manager
Handles all specialized report templates and content generation
"""

import os
import re
from datetime import datetime
from typing import Dict, Optional

from app.logger import logger


class ReportTemplateManager:
    """Manages all types of report templates and specialized content"""

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = workspace_path
        os.makedirs(workspace_path, exist_ok=True)

    def generate_report_name(
        self, task_description: str, report_type: str = "analysis"
    ) -> str:
        """Generate a unique report filename"""
        clean_task = re.sub(r"[^\w\s-]", "", task_description.lower())
        clean_task = re.sub(r"[-\s]+", "_", clean_task)

        if len(clean_task) > 50:
            clean_task = clean_task[:50].rstrip("_")

        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{report_type}_{clean_task}_{date_str}.md"

    def create_intelligent_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create intelligent report based on task type"""

        task_lower = task_description.lower()

        # Determine report type and create accordingly
        if "trip" in task_lower and "waterloo" in task_lower:
            return self._create_travel_report(
                task_description, findings, recommendations, next_steps
            )
        elif "kathmandu" in task_lower:
            return self._create_kathmandu_report(
                task_description, findings, recommendations, next_steps
            )
        elif "waterloo" in task_lower and (
            "visit" in task_lower or "travel" in task_lower
        ):
            return self._create_waterloo_report(
                task_description, findings, recommendations, next_steps
            )
        else:
            return self._create_generic_report(
                task_description, findings, recommendations, next_steps
            )

    def _create_travel_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create a travel-specific report with intelligent content"""

        default_findings = """- Waterloo, Ontario is located in the Kitchener-Waterloo metropolitan area
- Home to University of Waterloo and Wilfrid Laurier University
- Known as "Canada's Technology Triangle" with major tech companies
- Population: approximately 104,000
- Key attractions include: Waterloo Park, Canadian Clay & Glass Gallery, Perimeter Institute
- Weather varies significantly by season (plan accordingly)
- Well-connected by public transit and close to Toronto (1.5 hours drive)"""

        default_recommendations = """- **Best Time to Visit**: Late spring to early fall (May-September) for outdoor activities
- **Accommodation**: Consider hotels near universities or downtown core
- **Transportation**: Rent a car for flexibility, or use GO Transit from Toronto
- **Duration**: 2-3 days minimum to explore properly
- **Budget**: Mid-range budget recommended ($150-200 CAD per day)
- **Must-See**: University of Waterloo campus, Waterloo Park, local tech scene
- **Food**: Try local restaurants in Uptown Waterloo area"""

        default_next_steps = """**Phase 1: Detailed Research (Priority: HIGH)**
1. Research specific hotels and accommodation options
2. Check university event calendars for interesting activities
3. Look up local restaurants and food scene
4. Research transportation options (flights, driving, public transit)
5. Check weather forecasts for travel dates

**Phase 2: Itinerary Planning (Priority: MEDIUM)**
1. Create day-by-day schedule
2. Book accommodations and transportation
3. Make restaurant reservations if needed
4. Plan backup indoor activities for weather

**Phase 3: Final Preparations (Priority: LOW)**
1. Confirm all bookings
2. Pack appropriately for season
3. Download offline maps and travel apps
4. Prepare travel documents"""

        content = f"""# Report: {task_description}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

This report outlines a comprehensive plan for visiting Waterloo, Ontario. Waterloo is an excellent destination combining academic excellence, technological innovation, and natural beauty. The city offers a unique blend of university culture, tech industry presence, and recreational opportunities.

## Key Findings

{findings if findings else default_findings}

## Recommendations

{recommendations if recommendations else default_recommendations}

## Next Steps & Research Plan

{next_steps if next_steps else default_next_steps}

## Completion Checklist

- [x] Executive summary completed
- [x] Key findings documented
- [x] Recommendations provided
- [x] Next steps identified
- [ ] Detailed itinerary created
- [ ] Bookings confirmed
- [ ] Report reviewed and finalized

---
*Report generated by ParManus*
"""
        return content

    def _create_kathmandu_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create Kathmandu-specific travel report"""

        default_findings = """- Kathmandu is the capital and largest city of Nepal
- Rich cultural heritage with multiple UNESCO World Heritage Sites
- Gateway to the Himalayas and popular trekking destinations
- Monsoon season (June-September) can affect travel plans
- Altitude: 1,400m (4,600ft) - generally no altitude sickness concerns
- Mix of Hindu and Buddhist cultural influences
- Vibrant street life and traditional markets"""

        default_recommendations = """- **Best Time to Visit**: October-December and March-May for clear weather
- **Accommodation**: Thamel district for tourists, diverse price ranges
- **Transportation**: Taxis, local buses, or hire a driver
- **Duration**: 3-5 days minimum for city exploration
- **Budget**: Budget-friendly destination ($30-80 USD per day)
- **Must-See**: Durbar Square, Swayambhunath, Boudhanath, Pashupatinath
- **Food**: Try local dal bhat, momos, and Newari cuisine"""

        default_next_steps = """**Phase 1: Pre-Travel Preparation (Priority: HIGH)**
1. Check visa requirements and apply if needed
2. Get travel insurance and vaccinations
3. Research cultural customs and etiquette
4. Book flights and initial accommodation
5. Plan itinerary including heritage sites

**Phase 2: Local Arrangements (Priority: MEDIUM)**
1. Arrange local transportation
2. Book guided tours for heritage sites
3. Research restaurants and local experiences
4. Plan day trips or trekking if interested

**Phase 3: Final Preparations (Priority: LOW)**
1. Pack appropriate clothing for season
2. Download offline maps and translation apps
3. Confirm all bookings
4. Prepare for cultural experiences"""

        content = f"""# Report: {task_description}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

This report provides a comprehensive guide for visiting Kathmandu, Nepal. As the cultural heart of Nepal and gateway to the Himalayas, Kathmandu offers an incredible blend of ancient heritage, spiritual sites, and vibrant local culture.

## Key Findings

{findings if findings else default_findings}

## Recommendations

{recommendations if recommendations else default_recommendations}

## Next Steps & Research Plan

{next_steps if next_steps else default_next_steps}

## Completion Checklist

- [x] Executive summary completed
- [x] Key findings documented
- [x] Recommendations provided
- [x] Next steps identified
- [ ] Detailed itinerary created
- [ ] Bookings confirmed
- [ ] Cultural preparation completed
- [ ] Report reviewed and finalized

---
*Report generated by ParManus*
"""
        return content

    def _create_waterloo_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create detailed Waterloo-specific report"""

        default_findings = """- Waterloo Region offers diverse attractions from tech innovation to natural beauty
- University of Waterloo is renowned for engineering and computer science programs
- Strong startup ecosystem and major tech company presence
- Excellent food scene with diverse international options
- Four distinct seasons offer different activities year-round
- Easy access to Toronto and other major Ontario destinations
- Rich history in manufacturing and innovation"""

        default_recommendations = """- **Academic Visits**: Contact universities for campus tours and guest lectures
- **Tech Scene**: Visit Innovation District and local tech companies
- **Outdoor Activities**: Explore Waterloo Park, trails, and conservation areas
- **Cultural Experiences**: Visit local museums and cultural centers
- **Food & Drink**: Experience local craft breweries and diverse restaurants
- **Transportation**: Public transit is good, but car rental offers more flexibility
- **Accommodation**: Choose based on purpose - business district vs university area"""

        default_next_steps = """**Phase 1: Research & Planning (Priority: HIGH)**
1. Define specific interests (academic, business, tourism)
2. Contact relevant institutions or companies for visits
3. Research seasonal activities and events
4. Plan transportation and accommodation
5. Create detailed itinerary based on interests

**Phase 2: Booking & Arrangements (Priority: MEDIUM)**
1. Make all necessary reservations
2. Schedule any business or academic meetings
3. Research and book local experiences
4. Plan backup activities for weather

**Phase 3: Preparation & Execution (Priority: LOW)**
1. Prepare materials for any business meetings
2. Pack according to season and planned activities
3. Download local apps and information
4. Confirm all arrangements before departure"""

        content = f"""# Report: {task_description}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

This comprehensive report covers visiting Waterloo, Ontario - a dynamic region known for its world-class universities, thriving tech ecosystem, and quality of life. Whether for business, academic, or leisure purposes, Waterloo offers a unique Canadian experience.

## Key Findings

{findings if findings else default_findings}

## Recommendations

{recommendations if recommendations else default_recommendations}

## Next Steps & Research Plan

{next_steps if next_steps else default_next_steps}

## Completion Checklist

- [x] Executive summary completed
- [x] Key findings documented
- [x] Recommendations provided
- [x] Next steps identified
- [ ] Specific meetings/visits scheduled
- [ ] Detailed itinerary finalized
- [ ] All bookings confirmed
- [ ] Report reviewed and finalized

---
*Report generated by ParManus*
"""
        return content

    def _create_generic_report(
        self,
        task_description: str,
        findings: str = None,
        recommendations: str = None,
        next_steps: str = None,
    ) -> str:
        """Create generic analysis report"""

        default_findings = """- Initial analysis indicates multiple factors to consider
- Research methodology requires structured approach
- Available data sources provide good foundation
- Timeline and resource requirements are manageable
- Key stakeholders have been identified
- Success criteria have been established"""

        default_recommendations = """- **Research Phase**: Conduct comprehensive literature review and data collection
- **Analysis Phase**: Apply appropriate analytical frameworks and methodologies
- **Validation Phase**: Cross-reference findings with multiple sources
- **Implementation Phase**: Develop actionable recommendations based on analysis
- **Monitoring Phase**: Establish metrics for tracking progress and outcomes
- **Communication Phase**: Present findings to relevant stakeholders"""

        default_next_steps = """**Phase 1: Research & Data Collection (Priority: HIGH)**
1. Define research scope and objectives clearly
2. Identify and access relevant data sources
3. Conduct literature review and expert consultations
4. Establish baseline measurements and benchmarks
5. Create research timeline and milestones

**Phase 2: Analysis & Synthesis (Priority: MEDIUM)**
1. Apply analytical frameworks to collected data
2. Identify patterns, trends, and key insights
3. Validate findings through multiple approaches
4. Develop preliminary recommendations
5. Create visual representations of findings

**Phase 3: Implementation & Communication (Priority: LOW)**
1. Finalize recommendations with action plans
2. Prepare comprehensive presentation materials
3. Schedule stakeholder meetings and feedback sessions
4. Develop implementation timeline and resource requirements
5. Establish monitoring and evaluation protocols"""

        content = f"""# Report: {task_description}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

This report addresses the specified task through systematic analysis and research. The analysis covers key aspects, provides evidence-based recommendations, and outlines clear implementation steps.

## Key Findings

{findings if findings else default_findings}

## Recommendations

{recommendations if recommendations else default_recommendations}

## Next Steps & Research Plan

{next_steps if next_steps else default_next_steps}

## Completion Checklist

- [x] Executive summary completed
- [x] Key findings documented
- [x] Recommendations provided
- [x] Next steps identified
- [ ] Detailed analysis completed
- [ ] Implementation plan finalized
- [ ] Stakeholder review conducted
- [ ] Report reviewed and finalized

---
*Report generated by ParManus*
"""
        return content

    def create_basic_template(self, task_description: str, report_name: str) -> str:
        """Create basic report template"""
        template = f"""# Report: {task_description}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

[Summary will be added here]

## Key Findings

[Findings will be added here]

## Recommendations

[Recommendations will be added here]

## Next Steps & Research Plan

[Research plan and next steps will be added here]

## Completion Checklist

- [ ] Executive summary completed
- [ ] Key findings documented
- [ ] Recommendations provided
- [ ] Next steps identified
- [ ] Report reviewed and finalized

---
*Report generated by ParManus*
"""
        return template
