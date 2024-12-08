let tabsData = [];

function fetchCurrentWindowTabs() {
  chrome.tabs.query({ currentWindow: true }, (tabs) => {
    tabsData = tabs.map(tab => ({
      id: tab.id,
      title: tab.title,
      url: tab.url,
      favIconUrl: tab.favIconUrl
    }));
    displayTabs(tabsData);
  });
}

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

// Save tabs and group (if provided) to a JSON file
function saveTabsToJson() {
  const groupName = document.getElementById('group-name').value.trim();
  const timestamp = new Date().toISOString();

  const jsonData = {
    timestamp: timestamp,
    groups: groupName ? [{ name: groupName, tags: [] }] : [],
    tabs: tabsData.map(tab => ({
      id: tab.id,
      title: tab.title,
      url: tab.url,
      favIconUrl: tab.favIconUrl,
      group: groupName || null
    }))
  };

  const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const filename = groupName? `tabs_${groupName}.json` : `tabs.json`;

  chrome.downloads.download({
    url,
    filename,
  }, () => {
    window.close();
  });
}
// Focus on the group name input when the popup opens
function focusGroupNameInput() {
  const groupNameInput = document.getElementById('group-name');
  groupNameInput.focus();

  // Add event listener to save on Enter key press
  groupNameInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      saveTabsToJson();
    }
  });
}

// Populate tabs and focus on input when popup opens
document.addEventListener('DOMContentLoaded', () => {
  fetchCurrentWindowTabs();
  focusGroupNameInput();
});

document.getElementById('save-json').addEventListener('click', saveTabsToJson);