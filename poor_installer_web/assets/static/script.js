function showNotification(text) {
  const notification = document.getElementById('notification');
  const notificationText = document.getElementById('notification-text');
  notificationText.textContent = text;
  notification.classList.add('show');
  setTimeout(() => {
    notification.classList.remove('show');
  }, 2000);
}

function copyToClipboard(btn, command, actionType, toolName) {
  // Get the command text from the button's parent command box
  const commandBox = btn.closest('.command-box');
  const codeElement = commandBox.querySelector('code');
  const commandText = codeElement ? codeElement.textContent.trim() : command;
  
  // Try multiple clipboard methods for better mobile support
  if (navigator.clipboard && navigator.clipboard.writeText) {
    // Modern Clipboard API
    navigator.clipboard.writeText(commandText).then(() => {
      showSuccess(btn, actionType, toolName);
    }).catch(err => {
      console.log('Clipboard API failed, trying fallback:', err);
      fallbackCopyToClipboard(commandText, btn, actionType, toolName);
    });
  } else {
    // Fallback for older browsers
    fallbackCopyToClipboard(commandText, btn, actionType, toolName);
  }
}

function fallbackCopyToClipboard(text, btn, actionType, toolName) {
  // Create a temporary textarea for copying
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  document.body.appendChild(textArea);
  
  try {
    textArea.focus();
    textArea.select();
    textArea.setSelectionRange(0, 99999); // For mobile devices
    
    const successful = document.execCommand('copy');
    if (successful) {
      showSuccess(btn, actionType, toolName);
    } else {
      showNotification('Copy failed - please select and copy manually');
    }
  } catch (err) {
    console.log('Fallback copy failed:', err);
    showNotification('Copy not supported - please select and copy manually');
  } finally {
    document.body.removeChild(textArea);
  }
}

function showSuccess(btn, actionType, toolName) {
  const originalIcon = btn.innerHTML;
  btn.innerHTML = '<iconify-icon icon="mdi:check"></iconify-icon>';
  btn.classList.add('success');
  showNotification(`📋 Copied ${actionType} command for ${toolName}`);
  
  setTimeout(() => {
    btn.innerHTML = originalIcon;
    btn.classList.remove('success');
  }, 2000);
}