"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import { AsyncStateView } from "@/components/AsyncStateView";
import { StageBadge, StatusBadge } from "@/components/Badges";
import { useCandidates } from "@/hooks/useCandidates";
import {
  ALL_STAGES,
  ALL_STATUSES,
  STAGE_LABELS,
  STATUS_LABELS,
  type Candidate,
  type CandidateStage,
  type CandidateStatus,
} from "@/types";

function filterCandidates(
  candidates: Candidate[],
  search: string,
  status: CandidateStatus | "",
  stage: CandidateStage | "",
): Candidate[] {
  const query = search.trim().toLowerCase();

  return candidates.filter((candidate) => {
    const matchesSearch =
      !query ||
      candidate.full_name.toLowerCase().includes(query) ||
      candidate.email.toLowerCase().includes(query);
    const matchesStatus = !status || candidate.status === status;
    const matchesStage = !stage || candidate.stage === stage;
    return matchesSearch && matchesStatus && matchesStage;
  });
}

export function CandidateListPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { candidates, uiState, error, reload } = useCandidates();

  const statusParam = (searchParams.get("status") ?? "") as CandidateStatus | "";
  const stageParam = (searchParams.get("stage") ?? "") as CandidateStage | "";
  const [search, setSearch] = useState("");

  const updateQuery = useCallback(
    (key: "status" | "stage", value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
      router.replace(`/?${params.toString()}`, { scroll: false });
    },
    [router, searchParams],
  );

  const filtered = useMemo(
    () => filterCandidates(candidates, search, statusParam, stageParam),
    [candidates, search, statusParam, stageParam],
  );

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Active Recruitment Pipeline
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Review all clinical applicants across HealthCore&apos;s 12-clinic network.
          Filter by hiring status or pipeline stage.
        </p>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">
              Search by name or email
            </span>
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="e.g. Diane, nurse@healthcore.com"
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">
              Credential Status
            </span>
            <select
              value={statusParam}
              onChange={(event) => updateQuery("status", event.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
            >
              <option value="">All statuses</option>
              {ALL_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {STATUS_LABELS[status]}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">
              Pipeline Stage
            </span>
            <select
              value={stageParam}
              onChange={(event) => updateQuery("stage", event.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
            >
              <option value="">All stages</option>
              {ALL_STAGES.map((stage) => (
                <option key={stage} value={stage}>
                  {STAGE_LABELS[stage]}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <AsyncStateView uiState={uiState} error={error} onRetry={() => void reload()}>
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-3 text-sm text-slate-600">
            Showing {filtered.length} of {candidates.length} applicants
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">
                    Full Legal Name
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">
                    Clinical Role Applied
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">
                    Credential Status
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">
                    Pipeline Stage
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                      No applicants match the current filters.
                    </td>
                  </tr>
                ) : (
                  filtered.map((candidate) => (
                    <tr key={candidate.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">
                        {candidate.full_name}
                      </td>
                      <td className="px-4 py-3 text-slate-700">{candidate.position}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={candidate.status} />
                      </td>
                      <td className="px-4 py-3">
                        <StageBadge stage={candidate.stage} />
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          href={`/candidates/${candidate.id}`}
                          className="font-medium text-teal-700 hover:text-teal-900"
                        >
                          View profile
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </AsyncStateView>
    </div>
  );
}
