// Friendly messages under each field before a form is sent - the same idea as the
// Week 8 delivery form. It only helps people; the server (Django) checks everything
// again, because anyone can switch JavaScript off.
//
// Any <form data-validate> on the site uses it.

function explain(field) {
  const v = field.validity;
  if (v.valueMissing) return field.type === 'radio' ? 'Please choose one.' : 'Please fill in this field.';
  if (v.typeMismatch && field.type === 'email') return 'Enter a full email address, like name@campus.ac.ke.';
  if (v.patternMismatch) return field.title || 'Please check the format.';
  if (v.rangeOverflow) return 'The date cannot be in the future.';
  if (v.tooLong) return 'This is too long.';
  return field.validationMessage;
}

document.addEventListener('DOMContentLoaded', () => {
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
