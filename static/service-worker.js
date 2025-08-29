// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/static/service-worker.js')
      .then(function(registration) {
        console.log('ServiceWorker registration successful');
      }, function(err) {
        console.log('ServiceWorker registration failed: ', err);
      });
  });
}

// Handle install prompt
let deferredPrompt;
const installButton = document.getElementById('installButton');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  installButton.style.display = 'block';
});

installButton.addEventListener('click', async () => {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      installButton.style.display = 'none';
    }
    deferredPrompt = null;
  }
});