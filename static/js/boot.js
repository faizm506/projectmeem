/* adds the .js class before first paint so reveal animations only run when scripts work */
document.documentElement.classList.add('js');
/* safety net: if the main script never starts, show everything instead of leaving content hidden */
setTimeout(function () {
  if (!document.documentElement.classList.contains('ready')) document.documentElement.classList.add('reveal-all');
}, 6000);
