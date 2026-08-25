"use client";

import { useMemo, useState } from "react";
import {
  createIncident,
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
  type IncidentBranch,
  type IncidentCategory,
  type IncidentCreateInput,
  type IncidentOrigin,
  type IncidentStatus,
} from "@/lib/incidentApi";
import {
  BRANCH_LABELS,
  CATEGORY_LABELS,
  ORIGIN_LABELS,
  STATUS_LABELS,
} from "@/lib/incidentLabels";

type FormState = IncidentCreateInput;

type FieldErrors = Partial<Record<keyof FormState, string>>;

const INITIAL_STATE: FormState = {
  title: "",
  description: "",
  category: "technology",
  status: "open",
  origin: "internal",
  branch: "central",
};

export function IncidentRegistrationPanel() {
  const [form, setForm] = useState<FormState>(INITIAL_STATE);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isBranchOrigin = form.origin === "branch";

  const branchClassName = useMemo(() => {
    if (isBranchOrigin) {
      return "border border-amber-300 bg-amber-50";
    }
    return "border border-border bg-white";
  }, [isBranchOrigin]);

  function setValue<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => ({ ...prev, [key]: undefined }));
  }

  function validateClient(): FieldErrors {
    const errors: FieldErrors = {};
    if (!form.title.trim()) errors.title = "A title is required.";
    if (form.title.trim().length > 255) {
      errors.title = "The title must be 255 characters or fewer.";
    }
    if (!form.description.trim()) {
      errors.description = "A description is required.";
    }
    if (!form.category) errors.category = "Choose a category.";
    if (!form.status) errors.status = "Choose a status.";
    if (!form.origin) errors.origin = "Choose an origin.";
    if (!form.branch) errors.branch = "Choose a branch.";
    return errors;
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);

    const errors = validateClient();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await createIncident({
        ...form,
        title: form.title.trim(),
        description: form.description.trim(),
      });
      setForm(INITIAL_STATE);
      setFieldErrors({});
      setMessage("Incident created successfully.");
    } catch (err) {
      const typed = err as Error & { fieldErrors?: Record<string, string> };
      if (typed.fieldErrors) {
        setFieldErrors(typed.fieldErrors as FieldErrors);
      }
      setError(typed.message || "The incident could not be saved.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="border border-border bg-surface px-6 py-6">
      <h2 className="font-display text-2xl text-foreground">Register incident</h2>
      <p className="mt-2 text-sm text-muted">
        Create a new incident with validated HealthCore categories, origin, and branch.
      </p>

      <form className="mt-6 grid gap-4" onSubmit={onSubmit} noValidate>
        <div>
          <label className="text-sm font-medium text-foreground" htmlFor="title">
            Title
          </label>
          <input
            id="title"
            className="mt-1 w-full border border-border bg-white px-3 py-2 text-sm"
            value={form.title}
            onChange={(e) => setValue("title", e.target.value)}
            maxLength={255}
          />
          {fieldErrors.title ? (
            <p className="mt-1 text-xs text-red-700">{fieldErrors.title}</p>
          ) : null}
        </div>

        <div>
          <label className="text-sm font-medium text-foreground" htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            className="mt-1 min-h-28 w-full border border-border bg-white px-3 py-2 text-sm"
            value={form.description}
            onChange={(e) => setValue("description", e.target.value)}
          />
          {fieldErrors.description ? (
            <p className="mt-1 text-xs text-red-700">{fieldErrors.description}</p>
          ) : null}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-sm font-medium text-foreground" htmlFor="category">
              Category
            </label>
            <select
              id="category"
              className="mt-1 w-full border border-border bg-white px-3 py-2 text-sm"
              value={form.category}
              onChange={(e) => setValue("category", e.target.value as IncidentCategory)}
            >
              {INCIDENT_CATEGORIES.map((value) => (
                <option key={value} value={value}>
                  {CATEGORY_LABELS[value]}
                </option>
              ))}
            </select>
            {fieldErrors.category ? (
              <p className="mt-1 text-xs text-red-700">{fieldErrors.category}</p>
            ) : null}
          </div>

          <div>
            <label className="text-sm font-medium text-foreground" htmlFor="status">
              Status
            </label>
            <select
              id="status"
              className="mt-1 w-full border border-border bg-white px-3 py-2 text-sm"
              value={form.status}
              onChange={(e) => setValue("status", e.target.value as IncidentStatus)}
            >
              {INCIDENT_STATUSES.map((value) => (
                <option key={value} value={value}>
                  {STATUS_LABELS[value]}
                </option>
              ))}
            </select>
            {fieldErrors.status ? (
              <p className="mt-1 text-xs text-red-700">{fieldErrors.status}</p>
            ) : null}
          </div>

          <div>
            <label className="text-sm font-medium text-foreground" htmlFor="origin">
              Origin
            </label>
            <select
              id="origin"
              className="mt-1 w-full border border-border bg-white px-3 py-2 text-sm"
              value={form.origin}
              onChange={(e) => setValue("origin", e.target.value as IncidentOrigin)}
            >
              {INCIDENT_ORIGINS.map((value) => (
                <option key={value} value={value}>
                  {ORIGIN_LABELS[value]}
                </option>
              ))}
            </select>
            {fieldErrors.origin ? (
              <p className="mt-1 text-xs text-red-700">{fieldErrors.origin}</p>
            ) : null}
          </div>

          <div className={`px-3 py-2 ${branchClassName}`}>
            <label className="text-sm font-medium text-foreground" htmlFor="branch">
              Branch
            </label>
            <select
              id="branch"
              className="mt-1 w-full border border-border bg-white px-3 py-2 text-sm"
              value={form.branch}
              onChange={(e) => setValue("branch", e.target.value as IncidentBranch)}
            >
              {INCIDENT_BRANCHES.map((value) => (
                <option key={value} value={value}>
                  {BRANCH_LABELS[value]}
                </option>
              ))}
            </select>
            {fieldErrors.branch ? (
              <p className="mt-1 text-xs text-red-700">{fieldErrors.branch}</p>
            ) : null}
            {isBranchOrigin ? (
              <p className="mt-1 text-xs text-amber-900">
                Branch origin selected: confirm the reporting clinic before submitting.
              </p>
            ) : null}
          </div>
        </div>

        {error ? (
          <div className="border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
            {error}
          </div>
        ) : null}
        {message ? (
          <div className="border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
            {message}
          </div>
        ) : null}

        <div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sidebar-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Saving incident..." : "Create incident"}
          </button>
        </div>
      </form>
    </section>
  );
}
