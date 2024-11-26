let tabsData = [];

// Fetch tabs from the current window or all windows
function fetchTabs(currentWindow) {
  const queryOptions = currentWindow ? { currentWindow: true } : {};
  chrome.tabs.query(queryOptions, (tabs) => {
    tabsData = tabs.map(tab => ({
      id: tab.id,
      title: tab.title,
      url: tab.url,
      favIconUrl: tab.favIconUrl
    }));
    displayTabs(tabsData);
  });
}

// Display tabs in the popup
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

// Save tab data to a JSON file
function saveTabsToJson() {
    console.log("creating blob");
  if (tabsData.length === 0) {
    alert("No tab data available to save. Fetch tabs first!");
    return;
  }

  const blob = new Blob([JSON.stringify(tabsData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  chrome.downloads.download({
    url: url,
    filename: 'tabs.json',
    saveAs: true
  });
}

// Event listeners for buttons
document.getElementById('current-window').addEventListener('click', () => fetchTabs(true));
document.getElementById('all-windows').addEventListener('click', () => fetchTabs(false));
document.getElementById('save-json').addEventListener('click', saveTabsToJson);