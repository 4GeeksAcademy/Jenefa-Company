"use client";

import { useMemo, useRef, useState, type FormEvent } from "react";
import {
  clinicLocationsByCountry,
  type CountryCode,
} from "@/lib/site";
import {
  emptyApplicationValues,
  validateApplicationForm,
  validateField,
  type ApplicationField,
  type ApplicationFormValues,
  type FieldErrors,
} from "@/lib/applicationValidation";

type StatusTone = "idle" | "error" | "success" | "ready";

export function ApplicationForm() {
  const [values, setValues] = useState<ApplicationFormValues>(emptyApplicationValues);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [statusTone, setStatusTone] = useState<StatusTone>("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const dateInputRef = useRef<HTMLInputElement>(null);

  const clinicOptions = useMemo(() => {
    const country = values.country as CountryCode | "";
    if (country === "UK" || country === "US") {
      return clinicLocationsByCountry[country];
    }
    return clinicLocationsByCountry.US;
  }, [values.country]);

  function updateField<K extends ApplicationField>(field: K, value: ApplicationFormValues[K]) {
    setValues((current) => {
      const next = { ...current, [field]: value };
      if (field === "country") {
        next.clinicLocation = "";
      }
      return next;
    });
  }

  function validateSingle(field: ApplicationField) {
    const message = validateField(field, values);
    setErrors((current) => ({ ...current, [field]: message }));

    if (statusTone === "error") {
      const result = validateApplicationForm({
        ...values,
        [field]: values[field],
      });
      if (result.valid) {
        setStatusTone("ready");
        setStatusMessage("All fields are valid. You can submit the form now.");
      }
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = validateApplicationForm(values);
    setErrors(result.errors);

    if (!result.valid) {
      setStatusTone("error");
      setStatusMessage("Please correct the highlighted fields before submitting.");
      if (result.firstInvalid) {
        document.getElementById(result.firstInvalid)?.focus();
      }
      return;
    }

    setValues(emptyApplicationValues);
    setErrors({});
    setStatusTone("success");
    setStatusMessage("Application submitted successfully. Our team will contact you shortly.");
  }

  function handleReset() {
    setValues(emptyApplicationValues);
    setErrors({});
    setStatusTone("idle");
    setStatusMessage("");
  }

  function openDatePicker() {
    const input = dateInputRef.current;
    if (!input) return;
    input.focus();
    if (typeof input.showPicker === "function") {
      input.showPicker();
    }
  }

  const statusClassName =
    statusTone === "error"
      ? "mt-6 rounded-xl border border-rose-600 bg-rose-500/10 p-4 text-rose-700"
      : statusTone === "success" || statusTone === "ready"
        ? "mt-6 rounded-xl border border-emerald-400 bg-emerald-500/10 p-4 text-emerald-900"
        : "mt-6";

  return (
    <form
      id="applicationForm"
      noValidate
      aria-describedby="form-status"
      onSubmit={handleSubmit}
      onReset={handleReset}
      className="rounded-3xl border border-border bg-surface p-6 shadow-sm md:p-8"
    >
      <fieldset className="rounded-2xl border border-border p-4 md:p-5">
        <legend className="px-2 text-sm font-semibold text-foreground">
          Patient and appointment details
        </legend>
        <div className="grid gap-5 md:grid-cols-2">
          <Field
            id="firstName"
            label="First name"
            error={errors.firstName}
            value={values.firstName}
            onChange={(value) => updateField("firstName", value)}
            onBlur={() => validateSingle("firstName")}
          />
          <Field
            id="lastName"
            label="Last name"
            error={errors.lastName}
            value={values.lastName}
            onChange={(value) => updateField("lastName", value)}
            onBlur={() => validateSingle("lastName")}
          />
          <Field
            id="email"
            label="Email address"
            type="email"
            error={errors.email}
            value={values.email}
            onChange={(value) => updateField("email", value)}
            onBlur={() => validateSingle("email")}
          />
          <Field
            id="phone"
            label="Phone number"
            type="tel"
            error={errors.phone}
            value={values.phone}
            onChange={(value) => updateField("phone", value)}
            onBlur={() => validateSingle("phone")}
          />

          <SelectField
            id="country"
            label="Country"
            error={errors.country}
            value={values.country}
            onChange={(value) => {
              updateField("country", value);
              setErrors((current) => ({ ...current, clinicLocation: undefined }));
            }}
            onBlur={() => validateSingle("country")}
            options={[
              { value: "", label: "Choose country" },
              { value: "US", label: "United States" },
              { value: "UK", label: "United Kingdom" },
            ]}
          />

          <SelectField
            id="clinicLocation"
            label="Preferred clinic location"
            error={errors.clinicLocation}
            value={values.clinicLocation}
            onChange={(value) => updateField("clinicLocation", value)}
            onBlur={() => validateSingle("clinicLocation")}
            options={[
              { value: "", label: "Select location" },
              ...clinicOptions.map((location) => ({ value: location, label: location })),
            ]}
          />

          <div>
            <label htmlFor="preferredDate" className="block text-sm font-medium">
              Preferred appointment date
            </label>
            <div className="relative mt-2">
              <input
                ref={dateInputRef}
                id="preferredDate"
                name="preferredDate"
                type="date"
                required
                value={values.preferredDate}
                onChange={(event) => updateField("preferredDate", event.target.value)}
                onBlur={() => validateSingle("preferredDate")}
                aria-invalid={Boolean(errors.preferredDate)}
                className="w-full rounded-xl border border-slate-300 bg-surface px-4 py-3 pr-12 focus:border-accent-500 focus:outline-none"
              />
              <button
                type="button"
                aria-label="Open calendar"
                onClick={openDatePicker}
                className="absolute inset-y-0 right-0 inline-flex items-center justify-center rounded-r-xl px-3 text-foreground hover:text-accent-600 focus:outline-none focus:ring-2 focus:ring-accent-500"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  className="h-5 w-5"
                  aria-hidden="true"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
              </button>
            </div>
            {errors.preferredDate ? (
              <p className="mt-1 text-sm text-rose-600">{errors.preferredDate}</p>
            ) : null}
          </div>

          <SelectField
            id="contactMethod"
            label="Preferred contact method"
            error={errors.contactMethod}
            value={values.contactMethod}
            onChange={(value) => updateField("contactMethod", value)}
            onBlur={() => validateSingle("contactMethod")}
            options={[
              { value: "", label: "Select contact method" },
              { value: "Email", label: "Email" },
              { value: "Phone call", label: "Phone call" },
              { value: "SMS", label: "SMS" },
            ]}
          />
        </div>
      </fieldset>

      <fieldset className="mt-5 rounded-2xl border border-border p-4 md:p-5">
        <legend className="px-2 text-sm font-semibold text-foreground">Clinical information</legend>
        <div>
          <label htmlFor="healthSummary" className="block text-sm font-medium">
            Brief health summary
          </label>
          <textarea
            id="healthSummary"
            name="healthSummary"
            rows={4}
            required
            value={values.healthSummary}
            onChange={(event) => updateField("healthSummary", event.target.value)}
            onBlur={() => validateSingle("healthSummary")}
            aria-invalid={Boolean(errors.healthSummary)}
            className="mt-2 w-full rounded-xl border border-slate-300 bg-surface px-4 py-3 focus:border-accent-500 focus:outline-none"
          />
          {errors.healthSummary ? (
            <p className="mt-1 text-sm text-rose-600">{errors.healthSummary}</p>
          ) : null}
        </div>
      </fieldset>

      <fieldset className="mt-6 rounded-2xl border border-border p-4 md:p-5">
        <legend className="px-2 text-sm font-semibold text-foreground">Consent and confirmation</legend>
        <div className="space-y-3">
          <label className="flex items-start gap-3">
            <input
              id="consentData"
              name="consentData"
              type="checkbox"
              checked={values.consentData}
              onChange={(event) => updateField("consentData", event.target.checked)}
              onBlur={() => validateSingle("consentData")}
              aria-invalid={Boolean(errors.consentData)}
              className="mt-1 h-4 w-4 rounded border-slate-400 bg-surface text-accent-600 focus:ring-accent-600"
              required
            />
            <span className="text-sm text-muted">
              I consent to HealthCore processing my data under HIPAA/UK GDPR for care coordination.
            </span>
          </label>
          {errors.consentData ? (
            <p className="text-sm text-rose-600">{errors.consentData}</p>
          ) : null}

          <label className="flex items-start gap-3">
            <input
              id="nonEmergency"
              name="nonEmergency"
              type="checkbox"
              checked={values.nonEmergency}
              onChange={(event) => updateField("nonEmergency", event.target.checked)}
              onBlur={() => validateSingle("nonEmergency")}
              aria-invalid={Boolean(errors.nonEmergency)}
              className="mt-1 h-4 w-4 rounded border-slate-400 bg-surface text-accent-500 focus:ring-accent-500"
              required
            />
            <span className="text-sm text-muted">
              I confirm this request is not for a life-threatening emergency.
            </span>
          </label>
          {errors.nonEmergency ? (
            <p className="text-sm text-rose-600">{errors.nonEmergency}</p>
          ) : null}
        </div>
      </fieldset>

      <div id="form-status" className={statusClassName} aria-live="polite">
        {statusMessage}
      </div>

      <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <button
          type="submit"
          className="inline-flex min-w-44 justify-center rounded-full bg-accent-500 px-6 py-3 font-semibold text-white hover:bg-accent-600 focus:outline-none focus:ring-2 focus:ring-accent-500"
        >
          Submit
        </button>
        <button
          type="reset"
          className="inline-flex min-w-44 justify-center rounded-full bg-accent-500 px-6 py-3 font-semibold text-white hover:bg-accent-600 focus:outline-none focus:ring-2 focus:ring-accent-500"
        >
          Reset
        </button>
      </div>
    </form>
  );
}

function Field({
  id,
  label,
  value,
  error,
  onChange,
  onBlur,
  type = "text",
}: {
  id: string;
  label: string;
  value: string;
  error?: string;
  onChange: (value: string) => void;
  onBlur: () => void;
  type?: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        required
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onBlur={onBlur}
        aria-invalid={Boolean(error)}
        className="mt-2 w-full rounded-xl border border-slate-300 bg-surface px-4 py-3 focus:border-accent-500 focus:outline-none"
      />
      {error ? <p className="mt-1 text-sm text-rose-600">{error}</p> : null}
    </div>
  );
}

function SelectField({
  id,
  label,
  value,
  error,
  onChange,
  onBlur,
  options,
}: {
  id: string;
  label: string;
  value: string;
  error?: string;
  onChange: (value: string) => void;
  onBlur: () => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <select
        id={id}
        name={id}
        required
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onBlur={onBlur}
        aria-invalid={Boolean(error)}
        className="mt-2 w-full rounded-xl border border-slate-300 bg-surface px-4 py-3 focus:border-accent-500 focus:outline-none"
      >
        {options.map((option) => (
          <option key={`${option.value}-${option.label}`} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? <p className="mt-1 text-sm text-rose-600">{error}</p> : null}
    </div>
  );
}
