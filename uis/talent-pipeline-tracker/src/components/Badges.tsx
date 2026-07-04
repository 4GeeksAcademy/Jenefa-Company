import type { CandidateStage, CandidateStatus } from "@/types";
import { STAGE_LABELS, STATUS_LABELS } from "@/types";

const STATUS_COLORS: Record<CandidateStatus, string> = {
  received: "bg-slate-100 text-slate-800",
  in_progress: "bg-amber-100 text-amber-900",
  selected: "bg-emerald-100 text-emerald-900",
  discarded: "bg-red-100 text-red-900",
};

export function StatusBadge({ status }: { status: CandidateStatus }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_COLORS[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}

const STAGE_COLORS: Record<CandidateStage, string> = {
  pending: "bg-blue-50 text-blue-800",
  review: "bg-indigo-50 text-indigo-800",
  personal_interview: "bg-purple-50 text-purple-800",
  technical_interview: "bg-teal-50 text-teal-800",
  offer_presented: "bg-green-50 text-green-800",
};

export function StageBadge({ stage }: { stage: CandidateStage }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${STAGE_COLORS[stage]}`}
    >
      {STAGE_LABELS[stage]}
    </span>
  );
}
