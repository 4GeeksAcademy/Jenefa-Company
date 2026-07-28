export type ApplicationFormValues = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  country: string;
  clinicLocation: string;
  preferredDate: string;
  contactMethod: string;
  healthSummary: string;
  consentData: boolean;
  nonEmergency: boolean;
};

export type ApplicationField = keyof ApplicationFormValues;

export type FieldErrors = Partial<Record<ApplicationField, string>>;

type Validator = (value: ApplicationFormValues[ApplicationField]) => true | string;

const validators: Record<ApplicationField, Validator> = {
  firstName: (value) =>
    typeof value === "string" && value.trim().length >= 2
      ? true
      : "First name must have at least 2 characters.",
  lastName: (value) =>
    typeof value === "string" && value.trim().length >= 2
      ? true
      : "Last name must have at least 2 characters.",
  email: (value) =>
    typeof value === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
      ? true
      : "Enter a valid email address.",
  phone: (value) =>
    typeof value === "string" && /^\+?[0-9\s()-]{9,13}$/.test(value.trim())
      ? true
      : "Enter a valid phone number.",
  country: (value) =>
    typeof value === "string" && value !== "" ? true : "Please choose your country.",
  clinicLocation: (value) =>
    typeof value === "string" && value !== ""
      ? true
      : "Please choose a preferred clinic location.",
  preferredDate: (value) => {
    if (typeof value !== "string" || !value) return "Please choose a preferred date.";
    const selectedDate = new Date(`${value}T00:00:00`);
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return selectedDate >= now || "Preferred date cannot be in the past.";
  },
  contactMethod: (value) =>
    typeof value === "string" && value !== ""
      ? true
      : "Please choose your preferred contact method.",
  healthSummary: (value) =>
    typeof value === "string" && value.trim().length >= 20
      ? true
      : "Health summary must be at least 20 characters long.",
  consentData: (value) =>
    value === true || "You must consent to data processing.",
  nonEmergency: (value) =>
    value === true || "You must confirm this is not an emergency.",
};

export const emptyApplicationValues: ApplicationFormValues = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  country: "",
  clinicLocation: "",
  preferredDate: "",
  contactMethod: "",
  healthSummary: "",
  consentData: false,
  nonEmergency: false,
};

export function validateField(
  field: ApplicationField,
  values: ApplicationFormValues
): string | undefined {
  const result = validators[field](values[field]);
  return result === true ? undefined : result;
}

export function validateApplicationForm(values: ApplicationFormValues): {
  valid: boolean;
  errors: FieldErrors;
  firstInvalid?: ApplicationField;
} {
  const errors: FieldErrors = {};
  let firstInvalid: ApplicationField | undefined;

  (Object.keys(validators) as ApplicationField[]).forEach((field) => {
    const message = validateField(field, values);
    if (message) {
      errors[field] = message;
      if (!firstInvalid) firstInvalid = field;
    }
  });

  return {
    valid: Object.keys(errors).length === 0,
    errors,
    firstInvalid,
  };
}
