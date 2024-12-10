let tabsData = [];


// Fetch all tabs from the current window and generate timestamped URLs
async function fetchTabsWithTimestamp() {
  try {
    const tabs = await chrome.tabs.query({ currentWindow: true });
    tabsData = await Promise.all(
      tabs.map(async (tab) => {
        if (tab.url.includes("youtube.com/watch")) {
          const timestampedUrl = await getTimestampedUrl(tab.id);
          return {
            id: tab.id,
            title: tab.title,
            url: timestampedUrl || tab.url,
            favIconUrl: tab.favIconUrl,
          };
        } else {
          return {
            id: tab.id,
            title: tab.title,
            url: tab.url,
            favIconUrl: tab.favIconUrl,
          };
        }
      })
    );
    displayTabs(tabsData);
  } catch (error) {
    console.error("Error fetching tabs:", error);
  }
}

// Get the timestamped URL for a YouTube tab
async function getTimestampedUrl(tabId) {
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: () => {
        const video = document.querySelector("video");
        if (!video) return null;

        const time = Math.floor(video.currentTime);
        const url = new URL(window.location.href);
        url.searchParams.set("t", time);
        return url.toString();
      },
    });

    return result?.result || null;
  } catch (error) {
    console.error("Error executing script for tab ID:", tabId, error);
    return null;
  }
}

// Display tabs with their URLs in the popup
function displayTabs(tabs) {
  const tabsDiv = document.getElementById("tabs");
  tabsDiv.innerHTML = ""; // Clear previous results

  tabs.forEach((tab) => {
    const div = document.createElement("div");
    div.className = "tab-item";
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
    fetchTabsWithTimestamp()
    focusGroupNameInput();
});

document.getElementById('save-json').addEventListener('click', saveTabsToJson);