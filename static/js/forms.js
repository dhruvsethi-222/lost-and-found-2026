// Friendly messages under each field before a form is sent.
// It only helps people: the server (Django) checks everything again, because
// anyone can switch JavaScript off.
//
// Any <form data-validate> on the site uses it.

// Turns the browser's own check of one field into a plain message.
function explain(field) {
  const v = field.validity;
  if (v.valueMissing) return field.type === 'radio' ? 'Please choose one.' : 'Please fill in this field.';
  if (v.typeMismatch && field.type === 'email') return 'Enter a full email address, like name@strathmore.edu.';
  if (v.patternMismatch) return field.title || 'Please check the format.';
  if (v.rangeOverflow) return 'The date cannot be in the future.';
  if (v.tooLong) return 'This is too long.';
  return field.validationMessage;
}

// "Other" place: the "Specify the location" box is shown, and needed, only when "Other" is chosen.
// For every other place it is hidden (the server also empties it, see items/forms.py).
function setUpOtherPlace(box) {
  const place = document.getElementById(box.dataset.otherPlaceFor);
  const typed = box.querySelector('input, textarea');
  if (!place || !typed) return;
  const update = () => {
    const isOther = place.value === 'other';
    box.hidden = !isOther;
    typed.required = isOther;
  };
  place.addEventListener('change', update);
  update();                                  // also right away, e.g. after the server sent the form back
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-other-place-for]').forEach(setUpOtherPlace);

  document.querySelectorAll('form[data-validate]').forEach((form) => {
    form.setAttribute('novalidate', '');      // show our messages instead of the browser's pop-ups

    form.addEventListener('submit', (event) => {
      let firstProblem = null;
      form.querySelectorAll('input, select, textarea').forEach((field) => {
        if (field.type === 'hidden' || !field.name) return;
        const message = document.getElementById(`${field.name}-message`);
        if (!message) return;
        if (field.checkValidity()) {
          field.classList.remove('is-invalid');
          message.textContent = '';
        } else {
          message.textContent = explain(field);
          field.classList.add('is-invalid');
          firstProblem = firstProblem || field;
        }
      });
      if (firstProblem) {
        event.preventDefault();                // stop the form being sent
        firstProblem.focus();
      }
    });
  });
});
