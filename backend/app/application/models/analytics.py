# backend/app/application/models/analytics.py
from pydantic import BaseModel
from typing import List, Optional, Literal


# Trend Charts Models
class TrendMonthlyData(BaseModel):
    month: str
    contracts: int
    ambiguityRate: float


class TrendQualityScore(BaseModel):
    month: str
    score: float


class TrendContractType(BaseModel):
    type: str
    value: int
    ambiguity: float


class TrendAmbiguityByType(BaseModel):
    type: str
    ambiguity: float


class TrendChartData(BaseModel):
    monthlyData: List[TrendMonthlyData]
    qualityScores: List[TrendQualityScore]
    contractTypes: List[TrendContractType]
    ambiguityByType: List[TrendAmbiguityByType]


class TrendChartResponse(BaseModel):
    data: TrendChartData


# Recurring Phrases Models
class AmbiguousPhrase(BaseModel):
    id: str
    rank: int
    phrase: str
    description: str
    frequency: int
    maxFrequency: int
    status: str
    time: str


class RecurringPhrasesData(BaseModel):
    ambiguousPhrases: List[AmbiguousPhrase]


class RecurringPhrasesResponse(BaseModel):
    data: RecurringPhrasesData


# Contracts List Models
class ContractListItem(BaseModel):
    id: str
    name: str
    date: str
    type: str
    sentences: int
    ambiguityRate: float
    qualityScore: float
    tags: List[str]


class ContractsListResponse(BaseModel):
    items: List[ContractListItem]
    total: int


# Contract Stats Models
class ContractStatsResponse(BaseModel):
    totalContracts: int
    totalContractsChange: float
    analyzedSentences: int
    analyzedSentencesChange: float
    averageAmbiguityRate: float
    averageAmbiguityRateChange: float
    averageQualityScore: float
    averageQualityScoreChange: float


# Extracted Sentences Models
class SentenceItem(BaseModel):
    docId: str
    docName: str
    page: Optional[int]
    sentenceId: str
    text: str
    label: Optional[str]
    score: Optional[float]
    rationale: Optional[str]


class ExtractedSentencesResponse(BaseModel):
    sentences: List[SentenceItem]
class QualityData(BaseModel):
    month: str
    clarity: float
    completeness: float
    accuracy: float
    consistency: float

class AmbiguityTrend(BaseModel):
    month: str
    ambiguityRate: float
    targetRate: float = 10.0  # Fixed target rate

class ContractAnalysis(BaseModel):
    name: str
    totalSentences: int
    ambiguousSentences: int
    percentage: float

class ReportsData(BaseModel):
    stats: dict
    qualityMetrics: List[QualityData]
    ambiguityTrends: List[AmbiguityTrend]
    contractAnalysis: List[ContractAnalysis]

class ExportReportRequest(BaseModel):
    scope: Literal['all', 'current', 'custom'] = 'all'
    format: Literal['csv', 'excel'] = 'csv'
    includeCharts: bool = True
    includeSentenceData: bool = True
    includeExplanations: bool = True
    startDate: Optional[str] = None
    endDate: Optional[str] = None