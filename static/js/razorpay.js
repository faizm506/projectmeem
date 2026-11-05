/* Opens the Razorpay checkout window. Kept in its own file so the page needs no inline scripts (strict CSP). */
(() => {
  const btn = document.getElementById('payBtn');
  if (!btn) return;
  const d = btn.dataset, form = document.getElementById('verifyForm');
  btn.addEventListener('click', () => {
    if (typeof Razorpay === 'undefined') { alert('The payment window could not load. Please check your connection and try again.'); return; }
    new Razorpay({
      key: d.key, amount: +d.amount, currency: 'INR', name: 'MEEM', description: d.desc, order_id: d.order,
      prefill: { name: d.name, email: d.email, contact: d.phone }, theme: { color: '#245A48' },
      handler: r => {
        form.razorpay_order_id.value = r.razorpay_order_id;
        form.razorpay_payment_id.value = r.razorpay_payment_id;
        form.razorpay_signature.value = r.razorpay_signature;
        form.submit();
      }
    }).open();
  });
})();
