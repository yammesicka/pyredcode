firstButton = document.getElementById("controller-first");
backButton = document.getElementById("controller-back");
pauseButton = document.getElementById("controller-pause");
playButton = document.getElementById("controller-play");
nextButton = document.getElementById("controller-next");
lastButton = document.getElementById("controller-last");

function mod(n, m) {
  return ((n % m) + m) % m;
}

// Cache the getElement calls to speed up things a bit
memHtmlElement = Array.from(
  { length: memory.length },
  (_, i) => document.getElementById(`cell-${i}`),
);
playerInstHtmlElement = Array.from(
  { length: playerCount },
  (_, i) => Array.from({length: 5}, (_, j) => document.getElementById(`inst-${i}-${j}`)),
)
playerDeathHtmlElement = Array.from(
  { length: playerCount },
  (_, i) => document.querySelector(`#process-${i} .death-status`),
);

instruction = 0;

memoryHistory = Array.from(
  { length: memory.length },
  (_, address) => [{
    player: startMap[address],
    value: memory[address],
  }],
);
playerIpHistory = Array.from(
  moves.slice(0, playerCount),
  inst => [mod(inst.ip - 1, memory.length)],
);
memoryIpPointers = Array.from({ length: memory.length }, () => []);
playerIpHistory.forEach((ipHistory, pid) => {
  memoryIpPointers[ipHistory[0]].push(pid);
});
updateState(instruction);


function bgStyle(color) {
  return ((color === undefined) || (color === "undefined")) ?
    ['bg-gray-700', 'hover:bg-gray-600'] :
    [`bg-${color}-400`, `hover:bg-${color}-300`];
}

function borderStyle(color) {
  return ((color === undefined) || (color === "undefined")) ?
    [] :
    ['border-y-4', `border-${color}-600/75`, `hover:border-${color}-500/75`];
}

function updateCellMemValue(player, index, value) {
  const cell = memHtmlElement[index];
  const bgColor = colors[player];
  memory[index] = value;
  cell.classList.remove(...bgStyle(cell.dataset.bgColor));
  cell.classList.add(...bgStyle(bgColor));
  cell.dataset.bgColor = bgColor;
  cell.dataset.bgColor = bgColor;
}

function updateCellIp(player, index) {
  const cell = memHtmlElement[index];
  const borderColor = colors[player];
  cell.classList.remove(...borderStyle(cell.dataset.borderColor));
  cell.classList.add(...borderStyle(borderColor));
  cell.dataset.borderColor = borderColor;
}

function updatePlayerInstructions(pid, ip) {
  const startOffset = -2;
  for (let i = 0; i < 5; i++) {
    const current_ip = mod(ip + i + startOffset, memory.length);
    const inst = playerInstHtmlElement[pid][i];
    inst.innerText = memory.at(current_ip) || "???";
  }
}

function loadNextInstruction(instruction) {
  const {pid, ip, index, value} = moves[instruction];
  const previousIp = playerIpHistory[pid].at(-1);
  // remove the last instance of pid from memoryIpPointers[previousIp]
  const ipIndexToRemove = memoryIpPointers[previousIp].lastIndexOf(pid);
  memoryIpPointers[previousIp].splice(ipIndexToRemove, 1)

  const lastPlayerWithThisIp = memoryIpPointers[previousIp].at(-1);
  updateCellIp(lastPlayerWithThisIp, previousIp);

  memoryIpPointers[ip].push(pid);
  updateCellIp(pid, ip);
  playerIpHistory[pid].push(ip);

  memoryHistory[index].push({ player: pid, value });
  updateCellMemValue(pid, index, value);

  updatePlayerInstructions(pid, ip);
}


function updateLifeStatus(pid, instruction) {
  const player = document.getElementById(`process-${pid}`);
  if (instruction === null) {
    player.querySelector(".death-status").innerText = "💀";
    player.querySelector(".player-name").classList.add("line-through");
  } else {
    player.querySelector(".death-status").innerText = "";
    player.querySelector(".player-name").classList.remove("line-through");
  }
}

function updateState(ip) {
  if (ip !== undefined) {
    instruction = ip;
  }

  if (instruction === 0) {
    firstButton.disabled = true;
    backButton.disabled = true;
  } else {
    firstButton.disabled = false;
    backButton.disabled = false;
  }
  if (instruction === moves.length) {
    nextButton.disabled = true;
    lastButton.disabled = true;
  } else {
    nextButton.disabled = false;
    lastButton.disabled = false;
  }
}

nextButton.addEventListener("click", () => {
  updateLifeStatus(mod(instruction, playerCount), moves[instruction]);

  if (moves[instruction] === null) {
    updateState(instruction + 1);
    if (moves[instruction - playerCount - 1] === null) {
      // Go to the next player if died before the previous round
      nextButton.click();
    }
    return;
  }

  loadNextInstruction(instruction);
  updateState(instruction + 1);
});

lastButton.addEventListener("click", () => {
  while (!nextButton.disabled) {
    nextButton.click();
  }
});

function loadPreviousInstruction(instruction) {
  if (instruction < 0) return;

  const move = moves[instruction];
  if (move === null) {
    if (moves[instruction - playerCount] === null) {
      backButton.click();
    }
    return;
  }

  const {pid, index, value} = move;
  const lastMemEntry = memoryHistory[index].pop();  // Retrieve the last historical entry for this memory cell

  if (memoryHistory[index].length > 0) {
    const previousMemEntry = memoryHistory[index][memoryHistory[index].length - 1];  // Get the previous state from history
    updateCellMemValue(previousMemEntry.player, index, previousMemEntry.value);  // Restore the memory cell to its previous state
  } else {
    updateCellMemValue(null, index, memory[index]);  // Restore to the initial state if no previous modifications
  }

  const currentIp = playerIpHistory[pid].pop();
  const ipIndexToRemove = memoryIpPointers[currentIp].lastIndexOf(pid);
  if (ipIndexToRemove !== -1) {
    memoryIpPointers[currentIp].splice(ipIndexToRemove, 1);
  }

  // Update cell IP color based on the next PID in line for that IP, or clear it if none left
  const nextPlayerForIp = memoryIpPointers[currentIp].at(-1);
  if (nextPlayerForIp !== undefined) {
    updateCellIp(nextPlayerForIp, currentIp);
  } else {
    updateCellIp(null, currentIp); // Clear the IP marker if no players are left
  }

  // Handle visual update for the previous IP if available
  const previousIp = playerIpHistory[pid].at(-1);
  if (previousIp !== undefined) {
    updateCellIp(pid, previousIp);
  }
  updatePlayerInstructions(pid, previousIp);
}

backButton.addEventListener("click", () => {
  if (instruction <= 0) return;

  updateState(instruction - 1);
  if (instruction < playerCount) {  // First round
    updateLifeStatus(mod(instruction, playerCount), "alive");
  } else {
    updateLifeStatus(mod(instruction, playerCount), moves[instruction - playerCount]);
  }
  loadPreviousInstruction(instruction);
});

firstButton.addEventListener("click", () => {
  while (!backButton.disabled) {
    backButton.click();
  }
});
