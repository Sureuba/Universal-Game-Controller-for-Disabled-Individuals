const btnstartFSM = document.getElementById("startbtn");
const countdownContainer = document.querySelector(".countdown");
const iterNum = document.querySelector("inter-num");


const sections = {
  START: document.querySelector(".start"),
  COUNTDOWN: document.querySelector(".countdown"),
  RECORD: document.querySelector(".record"),
  BREAK: document.querySelector(".break"),
  CONFIRM: document.querySelector(".confirm")
};

//sleep function
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


function toggleContent(value) {
  value.hidden = !value.hidden;
}


btnstartFSM.onclick = async function(){
    //hide start, show countdown
    sections.START.classList.add('active');
    sections.COUNTDOWN.classList.add('active');
    
    for(let count = 10; count >= 0; count--){
        countdownContainer.innerHTML = count;
        await sleep(1000);
    }
    
    //hide countdown, show record
    sections.COUNTDOWN.classList.remove('active');
    sections.RECORD.classList.add('active');
    
    //start recording with progress bar (10 seconds)
    const recordDuration = 10000; //10 seconds in milliseconds
    const progressBar = document.getElementById('progressBar');
    const recordTimer = document.getElementById('recordTimer');
    const startTime = Date.now();
    
    const recordInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const progress = (elapsed / recordDuration) * 100;
        const seconds = Math.floor(elapsed / 1000);
        
        progressBar.style.width = Math.min(progress, 100) + '%';
        recordTimer.textContent = seconds + 's';
        
        if(elapsed >= recordDuration){
            clearInterval(recordInterval);
            progressBar.style.width = '100%';
            recordTimer.textContent = '10s';
            
            //after recording, show break section
            setTimeout(() => {
                sections.RECORD.classList.remove('active');
                sections.BREAK.classList.add('active');
                toggleContent(sections.CONFIRM);
            }, 500);
        }
    }, 10);
}






