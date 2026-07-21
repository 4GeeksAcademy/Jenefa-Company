"use client";

import Link from "next/link";
import { useState } from "react";
import { AsyncStateView } from "@/components/AsyncStateView";
import { StageBadge, StatusBadge } from "@/components/Badges";
import { NotesSection } from "@/components/NotesSection";
import { useCandidate } from "@/hooks/useCandidate";
import { patchRecord } from "@/services/records";
import {
  ALL_STAGES,
  ALL_STATUSES,
  STAGE_LABELS,
  STATUS_LABELS,
  type CandidateStage,
  type CandidateStatus,
} from "@/types";

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
const POSITION_LABELS: Record<string, string> = {
  "Licenciada/o en Administración de Empresas": "Business Administrator",
  "Asistente de Dirección": "Executive Assistant",
  "Técnica/o en Gestión y Organización": "Operations & Management Technician",
  "Secretaria/o Ejecutiva/o": "Executive Secretary",
  "Jefa/e de Gabinete": "Chief of Staff",
  "Coordinadora/or Administrativa/o": "Administrative Manager",
};

export function CandidateDetailPage({ id }: { id: string }) {
  const { candidate, uiState, error, reload, setCandidate } = useCandidate(id);
  const [patchError, setPatchError] = useState<string | null>(null);
  const [patchLoading, setPatchLoading] = useState(false);

  const handlePatch = async (
    field: "status" | "stage",
    value: CandidateStatus | CandidateStage,
  ) => {
    if (!candidate) return;
    setPatchLoading(true);
    setPatchError(null);
    try {
      const updated = await patchRecord(id, { [field]: value });
      setCandidate(updated);
    } catch (err) {
      setPatchError(
        err instanceof Error ? err.message : "Failed to update applicant record",
      );
    } finally {
      setPatchLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link href="/" className="text-sm font-medium text-teal-700 hover:text-teal-900">
          ← Back to candidate roster
        </Link>
        {candidate && (
          <Link
            href={`/candidates/${id}/edit`}
            className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
          >
            Edit applicant record
          </Link>
        )}
      </div>
 <div className="bg-slate-950 text-emerald-400 p-4 rounded text-xs font-mono border-2 border-red-500">
      <p className="font-bold text-white mb-2">🔍 SYSTEM DEBUG LOGS:</p>
      <p>• uiState: "{String(uiState)}"</p>
      <p>• hasError: "{String(!!error)}"</p>
      <p>• errorMessage: "{error?.message || "none"}"</p>
      <p>• candidateExists: "{String(!!candidate)}"</p>
    </div>
      <AsyncStateView
        uiState={uiState}
        error={error}
        loadingMessage="Loading applicant profile…"
        onRetry={() => void reload()}
      >
        {candidate && (
          <>
            <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-teal-700">
                    Applicant Profile
                  </p>
                  <h2 className="mt-1 text-2xl font-bold text-slate-900">
                    {candidate.full_name}
                  </h2>
                <div className="bg-slate-900 text-green-400 p-4 rounded text-xs font-mono my-2 overflow-auto max-h-40">
  <strong>Raw Candidate Data:</strong>
  <pre>{JSON.stringify(candidate, null, 2)}</pre>
</div> 
                  <p className="mt-1 text-slate-600">
                    {POSITION_LABELS[candidate.position] || candidate.position}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <StatusBadge status={candidate.status} />
                  <StageBadge stage={candidate.stage} />
                </div>
              </div>

              {patchError && (
                <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
                  {patchError}
                </p>
              )}

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <DetailField label="Email" value={candidate.email} />
                <DetailField label="Phone" value={candidate.phone} />
                <DetailField label="Clinical Role Applied" value={POSITION_LABELS[candidate.position] || candidate.position} />
                <DetailField
                  label="Years of Clinical Experience"
                  value={String(candidate.experience_years)}
                />
                <DetailField
                  label="Application Date"
                  value={formatDate(candidate.applied_at)}
                />
                <DetailField
                  label="LinkedIn Profile"
                  value={candidate.linkedin_url ?? "Not provided"}
                  href={candidate.linkedin_url ?? undefined}
                />
                <DetailField
                  label="CV / Resume"
                  value={candidate.cv_url ? "View document" : "Not provided"}
                  href={candidate.cv_url ?? undefined}
                />
              </div>

              <div className="mt-6 grid gap-4 border-t border-slate-200 pt-6 sm:grid-cols-2">
                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-slate-700">
                    Update Credential Status
                  </span>
                  <select
                    value={candidate.status}
                    disabled={patchLoading}
                    onChange={(event) =>
                      void handlePatch("status", event.target.value as CandidateStatus)
                    }
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600 disabled:opacity-60"
                  >
                    {ALL_STATUSES.map((status) => (
                      <option key={status} value={status}>
                        {STATUS_LABELS[status]}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-slate-700">
                    Update Pipeline Stage
                  </span>
                  <select
                    value={candidate.stage}
                    disabled={patchLoading}
                    onChange={(event) =>
                      void handlePatch("stage", event.target.value as CandidateStage)
                    }
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600 disabled:opacity-60"
                  >
                    {ALL_STAGES.map((stage) => (
                      <option key={stage} value={stage}>
                        {STAGE_LABELS[stage]}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </section>

            <NotesSection recordId={id} />
          </>
        )}
      </AsyncStateView>
    </div>
  );
}

function DetailField({
  label,
  value,
  href,
}: {
  label: string;
  value: string;
  href?: string;
}) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-slate-900">
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-teal-700 hover:underline"
          >
            {value}
          </a>
        ) : (
          value
        )}
      </dd>
    </div>
  );
}
