// Progressive enhancement: Django remains the source of cart data and prices.
document.documentElement.classList.add('js');
let timer;
const inputTimers = new WeakMap();
function notify(message) {
  const toast = document.querySelector('#toast'); toast.textContent = message; toast.hidden = false;
  clearTimeout(timer); timer = setTimeout(() => toast.hidden = true, 3500);
}
document.addEventListener('click', event => {
  const step = event.target.closest('[data-step]');
  if (!step) return;
  const form = step.closest('form'); const input = form.querySelector('[name="quantity"]');
  const quantity = Number(input.value) + Number(step.dataset.step);
  if (quantity >= 1 && quantity <= 99) { input.value = quantity; form.requestSubmit(); }
});
document.addEventListener('change', event => {
  if (event.target.matches('[name="quantity"]') && event.target.checkValidity()) {
    clearTimeout(inputTimers.get(event.target));
    event.target.form.requestSubmit();
  }
});
document.addEventListener('input', event => {
  const input = event.target;
  if (!input.matches('[name="quantity"]')) return;
  clearTimeout(inputTimers.get(input));
  if (input.checkValidity() && input.value !== '') {
    inputTimers.set(input, setTimeout(() => {
      if (input.isConnected) input.form.requestSubmit();
    }, 400));
  }
});
document.addEventListener('submit', async event => {
  const form = event.target;
  if (!form.matches('[data-cart-form]')) return;
  event.preventDefault();
  if (form.dataset.busy) return;
  form.dataset.busy = '1';
  const buttons = [...form.querySelectorAll('button')];
  const previous = buttons.map(button => button.disabled); buttons.forEach(button => button.disabled = true);
  try {
    const response = await fetch(form.action, {method:'POST', body:new FormData(form), headers:{Accept:'application/json'}, signal:AbortSignal.timeout(20000)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'მოქმედება ვერ შესრულდა.');
    if (data.reload) { location.reload(); return; }
    document.querySelector('[data-cart-count]').textContent = data.cart_count;
    if (data.html !== undefined && document.querySelector('#cart-content')) document.querySelector('#cart-content').innerHTML = data.html;
    notify(data.message);
  } catch (error) {
    notify(error.message && error.name === 'Error' ? error.message : 'კავშირი შეწყდა. განაახლე გვერდი, რათა გადაამოწმო კალათის მდგომარეობა.');
  } finally {
    delete form.dataset.busy; buttons.forEach((button,index) => button.disabled = previous[index]);
  }
});
document.addEventListener('error', event => {
  if (event.target.matches('img.food-image')) { event.target.alt = 'სურათი მიუწვდომელია'; event.target.removeAttribute('src'); }
}, true);
