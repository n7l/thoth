document.getElementById('current-window').addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'GET_TABS', currentWindow: true }, displayTabs);
  });

  document.getElementById('all-windows').addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'GET_TABS', currentWindow: false }, displayTabs);
  });

  function displayTabs(tabs) {
    const tabsDiv = document.getElementById('tabs');
    tabsDiv.innerHTML = ''; // Clear previous results

    tabs.forEach(tab => {
      const div = document.createElement('div');
      div.className = 'tab-item';
      div.innerHTML = `<strong>Title:</strong> ${tab.title}<br>
                       <strong>URL:</strong> <a href="${tab.url}" target="_blank">${tab.url}</a>`;
      tabsDiv.appendChild(div);
    });
  }