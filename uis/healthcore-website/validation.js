const form = document.getElementById('applicationForm');
const statusBox = document.getElementById('form-status');
const countryField = document.getElementById('country');
const clinicLocationField = document.getElementById('clinicLocation');
const preferredDateField = document.getElementById('preferredDate');
const openDatePickerButton = document.getElementById('openDatePicker');

const clinicLocationsByCountry = {
  UK: ['London', 'Manchester'],
  US: ['Austin', 'Houston', 'Miami', 'Atlanta']
};

const validators = {
  firstName: (value) => value.trim().length >= 2 || 'First name must have at least 2 characters.',
  lastName: (value) => value.trim().length >= 2 || 'Last name must have at least 2 characters.',
  email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || 'Enter a valid email address.',
  phone: (value) => /^\+?[0-9\s()-]{9,13}$/.test(value.trim()) || 'Enter a valid phone number.',
  country: (value) => value !== '' || 'Please choose your country.',
  clinicLocation: (value) => value !== '' || 'Please choose a preferred clinic location.',
  service: (value) => value !== '' || 'Please choose the service you need.',
  insuranceType: (value) => value !== '' || 'Please choose your insurance or payment type.',
  preferredDate: (value) => {
    if (!value) return 'Please choose a preferred date.';
    const selectedDate = new Date(`${value}T00:00:00`);
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return selectedDate >= now || 'Preferred date cannot be in the past.';
  },
  contactMethod: (value) => value !== '' || 'Please choose your preferred contact method.',
  healthSummary: (value) => value.trim().length >= 20 || 'Health summary must be at least 20 characters long.',
  consentData: (value) => value === true || 'You must consent to data processing.',
  nonEmergency: (value) => value === true || 'You must confirm this is not an emergency.'
};

function setFieldError(fieldName, message) {
  const field = document.getElementById(fieldName);
  const error = document.getElementById(`${fieldName}Error`);

  if (!field || !error) return;

  if (message) {
    field.setAttribute('aria-invalid', 'true');
    error.textContent = message;
    error.classList.remove('hidden');
  } else {
    field.removeAttribute('aria-invalid');
    error.textContent = '';
    error.classList.add('hidden');
  }
}

function getValue(fieldName) {
  const field = document.getElementById(fieldName);
  if (!field) return '';
  if (field.type === 'checkbox') return field.checked;
  return field.value;
}

function validateForm() {
  const fields = Object.keys(validators);
  const errors = [];

  fields.forEach((fieldName) => {
    const result = validators[fieldName](getValue(fieldName));
    if (result !== true) {
      errors.push({ fieldName, message: result });
      setFieldError(fieldName, result);
    } else {
      setFieldError(fieldName, '');
    }
  });

  return errors;
}

function updateClinicLocations() {
  if (!countryField || !clinicLocationField) return;

  const selectedCountry = countryField.value.trim().toUpperCase();
  const locationOptions = selectedCountry === 'UK'
    ? clinicLocationsByCountry.UK
    : clinicLocationsByCountry.US;

  clinicLocationField.innerHTML = '';

  const placeholderOption = document.createElement('option');
  placeholderOption.value = '';
  placeholderOption.textContent = 'Select location';
  clinicLocationField.appendChild(placeholderOption);

  locationOptions.forEach((location) => {
    const option = document.createElement('option');
    option.value = location;
    option.textContent = location;
    clinicLocationField.appendChild(option);
  });

  clinicLocationField.value = '';
  setFieldError('clinicLocation', '');
}

if (countryField) {
  countryField.addEventListener('change', updateClinicLocations);
}

updateClinicLocations();

if (openDatePickerButton && preferredDateField) {
  openDatePickerButton.addEventListener('click', () => {
    preferredDateField.focus();
    if (typeof preferredDateField.showPicker === 'function') {
      preferredDateField.showPicker();
    }
  });
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  statusBox.textContent = '';

  const errors = validateForm();

  if (errors.length > 0) {
    statusBox.className = 'mt-6 rounded-xl border border-rose-600 bg-rose-500/10 p-4 text-rose-700';
    statusBox.textContent = 'Please correct the highlighted fields before submitting.';
    const firstInvalid = document.getElementById(errors[0].fieldName);
    if (firstInvalid) firstInvalid.focus();
    return;
  }
  alert('Form submitted successfully!');
  form.reset();
  updateClinicLocations();
  statusBox.className = 'mt-6 rounded-xl border border-emerald-400 bg-emerald-500/10 p-4 text-emerald-200';
  statusBox.textContent = 'Application submitted successfully. Our team will contact you shortly.';
});

form.addEventListener('reset', () => {
  statusBox.className = 'mt-6';
  statusBox.textContent = '';

  Object.keys(validators).forEach((fieldName) => {
    setFieldError(fieldName, '');
  });

  
  setTimeout(() => {
    updateClinicLocations();
  }, 0);
});

Object.keys(validators).forEach((fieldName) => {
  const field = document.getElementById(fieldName);
  if (!field) return;

  const eventName = field.type === 'checkbox' || field.tagName === 'SELECT' ? 'change' : 'blur';
  field.addEventListener(eventName, () => {
    
    const result = validators[fieldName](getValue(fieldName));
    setFieldError(fieldName, result === true ? '' : result);
    
    const isShowingErrors = statusBox.classList.contains('bg-rose-500/10');
    
    if (isShowingErrors) {
      const allFields = Object.keys(validators);
      const hasAnyErrors = allFields.some((name) => validators[name](getValue(name)) !== true);

      if (!hasAnyErrors) {
        statusBox.className = 'mt-6 rounded-xl border border-emerald-400 bg-emerald-500/10 p-4 text-emerald-900';
        statusBox.textContent = 'All fields are valid. You can submit the form now.';
      }
    }
  });
});