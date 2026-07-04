"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { createRecord, replaceRecord } from "@/services/records";
import type { Candidate, RecordCreatePayload } from "@/types";

interface CandidateFormProps {
  mode: "create" | "edit";
  candidate?: Candidate;
}

interface FormFields {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  experience_years: string;
  linkedin_url: string;
  cv_url: string;
}

const emptyFields: FormFields = {
  full_name: "",
  email: "",
  phone: "",
  position: "",
  experience_years: "",
  linkedin_url: "",
  cv_url: "",
};

function fieldsFromCandidate(candidate: Candidate): FormFields {
  return {
    full_name: candidate.full_name,
    email: candidate.email,
    phone: candidate.phone,
    position: candidate.position,
    experience_years: String(candidate.experience_years),
    linkedin_url: candidate.linkedin_url ?? "",
    cv_url: candidate.cv_url ?? "",
  };
}

function validateFields(fields: FormFields): Record<string, string> {
  const errors: Record<string, string> = {};

  if (!fields.full_name.trim()) {
    errors.full_name = "Full legal name is required.";
  }
  if (!fields.email.trim()) {
    errors.email = "Email is required.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email.trim())) {
    errors.email = "Enter a valid email address.";
  }
  if (!fields.phone.trim()) {
    errors.phone = "Phone number is required.";
  }
  if (!fields.position.trim()) {
    errors.position = "Clinical role applied is required.";
  }
  if (!fields.experience_years.trim()) {
    errors.experience_years = "Years of experience is required.";
  } else if (
    Number.isNaN(Number(fields.experience_years)) ||
    Number(fields.experience_years) < 0
  ) {
    errors.experience_years = "Enter a valid number of years.";
  }

  return errors;
}

function toPayload(fields: FormFields): RecordCreatePayload {
  return {
    full_name: fields.full_name.trim(),
    email: fields.email.trim(),
    phone: fields.phone.trim(),
    position: fields.position.trim(),
    experience_years: Number(fields.experience_years),
    linkedin_url: fields.linkedin_url.trim() || null,
    cv_url: fields.cv_url.trim() || null,
  };
}

export function CandidateForm({ mode, candidate }: CandidateFormProps) {
  const router = useRouter();
  const [fields, setFields] = useState<FormFields>(
    candidate ? fieldsFromCandidate(candidate) : emptyFields,
  );
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitState, setSubmitState] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);

  const updateField = (key: keyof FormFields, value: string) => {
    setFields((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const errors = validateFields(fields);
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setSubmitState("error");
      setSubmitMessage("Please correct the highlighted fields before submitting.");
      return;
    }

    setSubmitState("loading");
    setSubmitMessage(null);

    try {
      const payload = toPayload(fields);
      if (mode === "create") {
        const created = await createRecord(payload);
        setSubmitState("success");
        setSubmitMessage("Applicant registered successfully.");
        router.push(`/candidates/${created.id}`);
      } else if (candidate) {
        await replaceRecord(candidate.id, payload);
        setSubmitState("success");
        setSubmitMessage("Applicant record updated successfully.");
        router.push(`/candidates/${candidate.id}`);
      }
    } catch (err) {
      setSubmitState("error");
      setSubmitMessage(
        err instanceof Error ? err.message : "Submission failed. Please try again.",
      );
    }
  };

  const title =
    mode === "create"
      ? "Register New Clinical Applicant"
      : "Edit Applicant Record";

  const description =
    mode === "create"
      ? "Add a new candidate to the HealthCore recruitment pipeline for Diane Foster's team."
      : "Correct applicant details when credentials or contact information changes.";

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <Link
        href={candidate ? `/candidates/${candidate.id}` : "/"}
        className="text-sm font-medium text-teal-700 hover:text-teal-900"
      >
        ← {candidate ? "Back to profile" : "Back to roster"}
      </Link>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-slate-900">{title}</h2>
        <p className="mt-1 text-sm text-slate-600">{description}</p>

        <form onSubmit={(event) => void handleSubmit(event)} className="mt-6 space-y-4">
          <FormInput
            label="Full Legal Name"
            value={fields.full_name}
            error={fieldErrors.full_name}
            onChange={(value) => updateField("full_name", value)}
            required
          />
          <FormInput
            label="Email"
            type="email"
            value={fields.email}
            error={fieldErrors.email}
            onChange={(value) => updateField("email", value)}
            required
          />
          <FormInput
            label="Phone"
            value={fields.phone}
            error={fieldErrors.phone}
            onChange={(value) => updateField("phone", value)}
            required
          />
          <FormInput
            label="Clinical Role Applied"
            value={fields.position}
            error={fieldErrors.position}
            onChange={(value) => updateField("position", value)}
            required
          />
          <FormInput
            label="Years of Clinical Experience"
            type="number"
            min="0"
            step="0.5"
            value={fields.experience_years}
            error={fieldErrors.experience_years}
            onChange={(value) => updateField("experience_years", value)}
            required
          />
          <FormInput
            label="LinkedIn Profile URL"
            value={fields.linkedin_url}
            onChange={(value) => updateField("linkedin_url", value)}
          />
          <FormInput
            label="CV / Resume URL"
            value={fields.cv_url}
            onChange={(value) => updateField("cv_url", value)}
          />

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={submitState === "loading"}
              className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-60"
            >
              {submitState === "loading"
                ? "Submitting…"
                : mode === "create"
                  ? "Register applicant"
                  : "Save changes"}
            </button>
            {submitState === "success" && submitMessage && (
              <p className="text-sm text-emerald-700">{submitMessage}</p>
            )}
            {submitState === "error" && submitMessage && (
              <p className="text-sm text-red-700">{submitMessage}</p>
            )}
          </div>
        </form>
      </section>
    </div>
  );
}

function FormInput({
  label,
  value,
  onChange,
  error,
  type = "text",
  required = false,
  min,
  step,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  type?: string;
  required?: boolean;
  min?: string;
  step?: string;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">
        {label}
        {required && <span className="text-red-600"> *</span>}
      </span>
      <input
        type={type}
        value={value}
        min={min}
        step={step}
        onChange={(event) => onChange(event.target.value)}
        className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-1 ${
          error
            ? "border-red-400 focus:border-red-500 focus:ring-red-500"
            : "border-slate-300 focus:border-teal-600 focus:ring-teal-600"
        }`}
      />
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  );
}
