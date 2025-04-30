// Floating timer (quiz.html)

document.addEventListener("DOMContentLoaded", () => {
    // Only run the timer on the quiz page
    const timerElement = document.getElementById("floating-timer");
    if (!timerElement) return;

    // Calculate time based on number of questions and difficulty
    const questionContainers = document.querySelectorAll('.question-answer-container');
    const numQuestions = questionContainers.length;
    
    // Define time per question based on difficulty levels
    const difficultyTimeMap = {
        "Easy": 15,
        "Moderate": 25,
        "Challenging": 40,
        "Very Difficult": 60,
        "Impossible": 90,
        "Gradual": 30
    };
    
    // Get the difficulty from the quiz container
    const quizContainer = document.querySelector('.quiz-container');
    const difficulty = quizContainer ? quizContainer.dataset.difficulty : 'Gradual';
    
    // Calculate seconds per question based on difficulty
    const secondsPerQuestion = difficultyTimeMap[difficulty];
    
    // Determine the timer duration
    let timerDuration = numQuestions * secondsPerQuestion;
    let remainingTime = timerDuration;

    const updateTimer = () => {
        const hours = Math.floor(remainingTime / 3600);
        const minutes = Math.floor((remainingTime % 3600) / 60);
        const seconds = remainingTime % 60;
        
        // Format with hours if needed, otherwise just show minutes:seconds
        if (hours > 0) {
            timerElement.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        } else {
            timerElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }
        
        remainingTime--;

        if (remainingTime < 0) {
            clearInterval(timerInterval);
            // Submit the form instead of redirecting
            const quizForm = document.querySelector('form');
            if (quizForm) {
                // Display a brief message that time is up
                const timeUpMessage = document.createElement('div');
                timeUpMessage.textContent = 'Time is up! Submitting your answers...';
                timeUpMessage.style.color = 'white';
                timeUpMessage.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
                timeUpMessage.style.padding = '10px';
                timeUpMessage.style.borderRadius = '5px';
                timeUpMessage.style.position = 'fixed';
                timeUpMessage.style.top = '50%';
                timeUpMessage.style.left = '50%';
                timeUpMessage.style.transform = 'translate(-50%, -50%)';
                timeUpMessage.style.zIndex = '1001';
                document.body.appendChild(timeUpMessage);
                
                // Submit the form after a short delay to show the message
                setTimeout(() => {
                    quizForm.submit();
                }, 1500);
            }
        }
    };

    const timerInterval = setInterval(updateTimer, 1000);
    updateTimer(); // Initialize the timer display immediately
});

