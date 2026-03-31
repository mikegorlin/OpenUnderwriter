"""Pydantic state models for D&O underwriting analysis.

Public API: Import all models from this package.

Usage:
    from do_uw.models import AnalysisState, SourcedValue, Confidence
"""

from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
    AISubDimension,
)
from do_uw.models.classification import ClassificationResult, MarketCapTier
from do_uw.models.common import (
    Confidence,
    DataFreshness,
    SourcedValue,
    StageResult,
    StageStatus,
)
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.density import DensityLevel, PreComputedNarratives, SectionDensity
from do_uw.models.executive_risk import (
    BoardAggregateRisk,
    IndividualRiskScore,
)
from do_uw.models.executive_summary import (
    CompanySnapshot,
    DealContext,
    ExecutiveSummary,
    InherentRiskBaseline,
    KeyFinding,
    KeyFindings,
    UnderwritingThesis,
)
from do_uw.models.financials import (
    AuditProfile,
    DistressIndicators,
    DistressResult,
    DistressZone,
    ExtractedFinancials,
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
    PeerCompany,
    PeerGroup,
)
from do_uw.models.forensic import (
    CashFlowQualityScore,
    FinancialIntegrityScore,
    ForensicZone,
    RevenueQualityScore,
    SubScore,
)
from do_uw.models.governance import (
    BoardProfile,
    CompensationFlags,
    GovernanceData,
)
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    GovernanceQualityScore,
    LeadershipForensicProfile,
    LeadershipStability,
    NarrativeCoherence,
    OwnershipAnalysis,
    SentimentProfile,
)
from do_uw.models.hazard_profile import (
    CategoryScore,
    HazardCategory,
    HazardDimensionScore,
    HazardProfile,
    InteractionEffect,
)
from do_uw.models.litigation import (
    CaseDetail,
    CaseStatus,
    CoverageType,
    EnforcementStage,
    LegalTheory,
    LitigationLandscape,
    SECEnforcement,
    SECEnforcementPipeline,
)
from do_uw.models.litigation_details import (
    ContingentLiability,
    DealLitigation,
    DefenseAssessment,
    ForumProvisions,
    IndustryClaimPattern,
    LitigationTimelineEvent,
    RegulatoryProceeding,
    SOLWindow,
    WhistleblowerIndicator,
    WorkforceProductEnvironmental,
)
from do_uw.models.market import (
    InsiderTradingProfile,
    MarketSignals,
    ShortInterestProfile,
    StockPerformance,
)
from do_uw.models.market_events import (
    AdverseEventScore,
    AnalystSentimentProfile,
    CapitalMarketsActivity,
    CapitalMarketsOffering,
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
    InsiderClusterEvent,
    InsiderTradingAnalysis,
    InsiderTransaction,
    StockDropAnalysis,
    StockDropEvent,
)
from do_uw.models.peril import (
    BearCase,
    EvidenceItem,
    PerilMap,
    PerilProbabilityBand,
    PerilSeverityBand,
    PlaintiffAssessment,
    PlaintiffFirmMatch,
)
from do_uw.models.scoring import (
    BenchmarkResult,
    FactorScore,
    MetricBenchmark,
    PatternMatch,
    RedFlagResult,
    ScoringResult,
    Tier,
    TierClassification,
    _rebuild_scoring_models,
)
from do_uw.models.state import (
    PIPELINE_STAGES,
    AcquiredData,
    AnalysisResults,
    AnalysisState,
    ExtractedData,
)
from do_uw.models.temporal import (
    TemporalAnalysisResult,
    TemporalClassification,
    TemporalDataPoint,
    TemporalSignal,
)

# Resolve forward references in ScoringResult (ScoringLensResult, etc.)
_rebuild_scoring_models()

__all__ = [
    # AI Risk (SECT8)
    "AICompetitivePosition",
    "AIDisclosureData",
    "AIPatentActivity",
    "AIRiskAssessment",
    "AISubDimension",
    # State (root)
    "AcquiredData",
    "AdverseEventScore",
    "AnalysisResults",
    "AnalysisState",
    "AnalystSentimentProfile",
    "AuditProfile",
    # Peril mapping
    "BearCase",
    # Scoring
    "BenchmarkResult",
    # Executive Risk
    "BoardAggregateRisk",
    # Governance
    "BoardForensicProfile",
    "BoardProfile",
    "CapitalMarketsActivity",
    "CapitalMarketsOffering",
    # Litigation
    "CaseDetail",
    "CaseStatus",
    # Forensic composites
    "CashFlowQualityScore",
    # Classification (Layer 1)
    "ClassificationResult",
    # Hazard Profile (Layer 2)
    "CategoryScore",
    # Company
    "CompanyIdentity",
    "CompanyProfile",
    # Executive Summary
    "CompanySnapshot",
    "CompensationAnalysis",
    "CompensationFlags",
    # Common types
    "Confidence",
    "ContingentLiability",
    "CoverageType",
    "DataFreshness",
    "DealContext",
    # Density (Phase 35)
    "DensityLevel",
    "DealLitigation",
    "DefenseAssessment",
    "DistressIndicators",
    "DistressResult",
    "DistressZone",
    "EarningsGuidanceAnalysis",
    "EarningsQuarterRecord",
    "EnforcementStage",
    "EvidenceItem",
    "ExecutiveSummary",
    "ExtractedData",
    "ExtractedFinancials",
    "FactorScore",
    "FinancialIntegrityScore",
    "FinancialLineItem",
    "FinancialStatement",
    "FinancialStatements",
    "ForensicZone",
    "ForumProvisions",
    "GovernanceData",
    "GovernanceQualityScore",
    "HazardCategory",
    "HazardDimensionScore",
    "HazardProfile",
    "IndividualRiskScore",
    "IndustryClaimPattern",
    "InherentRiskBaseline",
    "InsiderClusterEvent",
    "InsiderTradingAnalysis",
    "InsiderTradingProfile",
    "InsiderTransaction",
    "InteractionEffect",
    "KeyFinding",
    "KeyFindings",
    "LeadershipForensicProfile",
    "LeadershipStability",
    "LegalTheory",
    "LitigationLandscape",
    "LitigationTimelineEvent",
    "MarketCapTier",
    "MarketSignals",
    "MetricBenchmark",
    "NarrativeCoherence",
    "OwnershipAnalysis",
    "PatternMatch",
    "PeerCompany",
    "PeerGroup",
    "PerilMap",
    "PerilProbabilityBand",
    "PerilSeverityBand",
    "PIPELINE_STAGES",
    "PlaintiffAssessment",
    "PlaintiffFirmMatch",
    "PreComputedNarratives",
    "RedFlagResult",
    "RegulatoryProceeding",
    "RevenueQualityScore",
    "SECEnforcement",
    "SECEnforcementPipeline",
    "SOLWindow",
    "ScoringResult",
    "SectionDensity",
    "SentimentProfile",
    "ShortInterestProfile",
    "SourcedValue",
    "StageResult",
    "StageStatus",
    "StockDropAnalysis",
    "StockDropEvent",
    "StockPerformance",
    "SubScore",
    # Temporal analysis
    "TemporalAnalysisResult",
    "TemporalClassification",
    "TemporalDataPoint",
    "TemporalSignal",
    "Tier",
    "TierClassification",
    "UnderwritingThesis",
    "WhistleblowerIndicator",
    "WorkforceProductEnvironmental",
]
