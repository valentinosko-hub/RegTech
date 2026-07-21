// Shared type definitions for RegOps Hub. These mirror the Lakebase/Delta
// data model documented in ARCHITECTURE.md so that the shapes returned by
// mock services in Phase 1 are identical to what real queries will return
// in Phase 2/3.

export type Jurisdiction = 'ASIC' | 'MiFID' | 'EMIR' | 'FCA' | 'MAS';

export type Vendor = 'Cappitech' | 'Kaizen' | 'UnaVista' | 'DTCC';

export type Severity = 'P1' | 'P2' | 'P3' | 'P4';

export type CaseStatus = 'open' | 'investigating' | 'pending_vendor' | 'closed';

export type CaseType = 'incident' | 'task' | 'query';

export type CaseSourceType = 'monitoring_alert' | 'recon_break' | 'paste' | 'manual';

export type ResolutionType =
  | 'mapping_applied'
  | 'resolved_with_note'
  | 'false_positive'
  | 'escalated_to_case';

// ---------------------------------------------------------------------------
// Monitoring
// ---------------------------------------------------------------------------

export type ReportStatus =
  | 'scheduled'
  | 'generating'
  | 'validating'
  | 'queued'
  | 'submitted'
  | 'acknowledged'
  | 'failed'
  | 'resubmitted';

export interface ReportSubmission {
  submissionId: string;
  reportName: string;
  jurisdiction: Jurisdiction;
  reportingPeriod: string;
  status: ReportStatus;
  dueTime: string;
  startedAt: string | null;
  submittedAt: string | null;
  acknowledgedAt: string | null;
  slaMet: boolean | null;
  recordCount: number | null;
  errorMessage: string | null;
  slaState: 'on_track' | 'at_risk' | 'breached' | 'met' | null;
  estimatedCompletion: string | null;
}

export type FeedHealth = 'healthy' | 'delayed' | 'failed';

export interface FeedStatusItem {
  vendor: Vendor;
  status: FeedHealth;
  lastReceivedAt: string;
  expectedCadenceMinutes: number;
  delayMinutes: number;
}

export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertEventType =
  | 'feed_delay'
  | 'feed_failure'
  | 'volume_anomaly'
  | 'sla_warning'
  | 'sla_breach'
  | 'report_status_change';
export type AlertStatus = 'active' | 'resolved' | 'escalated';

export interface Alert {
  eventId: string;
  eventType: AlertEventType;
  sourceVendor: Vendor | null;
  sourceReport: string | null;
  severity: AlertSeverity;
  description: string;
  aiAssessment: string | null;
  status: AlertStatus;
  detectedAt: string;
  resolvedAt: string | null;
}

export interface AlertHistoryPoint {
  date: string;
  lateByMinutes: number;
  recoveryMinutes: number;
}

export interface AlertDetail extends Alert {
  historicalSummary: string;
  lateCountLast30Days: number;
  avgRecoveryMinutes: number;
  recommendedAction: string;
  history: AlertHistoryPoint[];
  linkedCaseId: string | null;
}

// ---------------------------------------------------------------------------
// Reconciliation
// ---------------------------------------------------------------------------

export type ReconRunStatus = 'completed' | 'reviewed' | 'signed_off';

export interface ReconRun {
  runId: string;
  reconSetName: string;
  jurisdiction: Jurisdiction;
  runDate: string;
  sourceCount: number;
  targetCount: number;
  matchedCount: number;
  breakCount: number;
  openBreakCount: number;
  matchRate: number;
  status: ReconRunStatus;
  reviewedBy: string | null;
  signedOffAt: string | null;
}

export type BreakCategory =
  | 'known_mapping'
  | 'value_mismatch'
  | 'date_discrepancy'
  | 'missing_record'
  | 'extra_record'
  | 'novel';

export type BreakStatus = 'open' | 'resolved' | 'escalated';

export interface ReconBreak {
  breakId: string;
  runId: string;
  reconSetName: string;
  jurisdiction: Jurisdiction;
  fieldName: string;
  sourceValue: string;
  targetValue: string;
  sourceRecord: Record<string, string>;
  targetRecord: Record<string, string>;
  category: BreakCategory | null;
  historicalFrequency: number;
  aiExplanation: string | null;
  status: BreakStatus;
  resolutionType: ResolutionType | null;
  resolutionNote: string | null;
  resolvedBy: string | null;
  resolvedAt: string | null;
  linkedCaseId: string | null;
  linkedMappingRuleId: string | null;
  createdAt: string;
}

export interface MappingRule {
  id: string;
  fieldPattern: string;
  sourcePattern: string;
  targetPattern: string;
  resolutionDescription: string;
}

export interface BulkResolveResult {
  updated: ReconBreak[];
  failedBreakIds: string[];
}

// ---------------------------------------------------------------------------
// Cases
// ---------------------------------------------------------------------------

export interface Case {
  caseId: string;
  title: string;
  description: string | null;
  status: CaseStatus;
  severity: Severity;
  jurisdiction: Jurisdiction | null;
  vendor: Vendor | null;
  caseType: CaseType;
  owner: string;
  sourceType: CaseSourceType;
  sourceRef: string | null;
  resolutionType: string | null;
  resolutionNote: string | null;
  createdAt: string;
  updatedAt: string;
  closedAt: string | null;
}

export type TimelineEventType =
  | 'created'
  | 'status_changed'
  | 'severity_changed'
  | 'comment_added'
  | 'escalated'
  | 'closed'
  | 'linked';

export interface TimelineEvent {
  id: string;
  caseId: string;
  eventType: TimelineEventType;
  actor: string;
  description: string;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface Comment {
  id: string;
  caseId: string;
  author: string;
  body: string;
  createdAt: string;
}

export interface LinkedItem {
  type: 'alert' | 'break';
  id: string;
  label: string;
  href: string;
}

export interface CaseDetail extends Case {
  timeline: TimelineEvent[];
  comments: Comment[];
  linkedItems: LinkedItem[];
}

export type FieldConfidence = 'confident' | 'suggested' | 'unknown';

export interface ExtractedField<T> {
  value: T | null;
  confidence: FieldConfidence;
}

export interface CaseExtraction {
  status: 'ok' | 'failed';
  title: ExtractedField<string>;
  severity: ExtractedField<Severity>;
  jurisdiction: ExtractedField<Jurisdiction>;
  vendor: ExtractedField<Vendor>;
  caseType: ExtractedField<CaseType>;
  description: ExtractedField<string>;
  duplicateWarning: { caseId: string; title: string } | null;
}

export interface CreateCasePayload {
  title: string;
  description?: string | null;
  severity: Severity;
  jurisdiction?: Jurisdiction | null;
  vendor?: Vendor | null;
  caseType: CaseType;
  sourceType: CaseSourceType;
  sourceRef?: string | null;
}

// ---------------------------------------------------------------------------
// Home
// ---------------------------------------------------------------------------

export interface ReconSummaryRow {
  reconSetName: string;
  jurisdiction: Jurisdiction;
  breakCount: number;
  matchRate: number;
  status: 'clean' | 'breaks';
  runId: string;
}

export interface HomeSummary {
  overnightSummary: string;
  briefingGeneratedAt: string;
  reportStatus: ReportSubmission[];
  feedStatus: FeedStatusItem[];
  reconSummary: ReconSummaryRow[];
  activeAlerts: Alert[];
  openCases: {
    count: number;
    cases: Case[];
  };
}

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export type NotificationType =
  | 'alert_fired'
  | 'case_assigned'
  | 'report_submitted'
  | 'recon_completed';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string | null;
  link: string | null;
  read: boolean;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Saved views / command bar
// ---------------------------------------------------------------------------

export type SavedViewId =
  | 'todays_reports'
  | 'todays_reconciliation'
  | 'todays_breaks'
  | 'active_alerts'
  | 'my_open_cases'
  | 'awaiting_vendor'
  | 'late_reports';

export interface SavedViewCounts {
  todaysReports: number;
  todaysReconciliation: number;
  todaysBreaks: number;
  activeAlerts: number;
  myOpenCases: number;
  awaitingVendor: number;
  lateReports: number;
}

export interface CurrentUser {
  id: string;
  displayName: string;
  email: string;
  role: 'analyst' | 'lead' | 'admin';
}

export interface SearchResult {
  type: 'case' | 'run' | 'alert';
  id: string;
  label: string;
  sublabel: string;
  href: string;
}
