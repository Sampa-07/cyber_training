// Mandatory Quiz with Progression Control
document.getElementById('securityQuiz').addEventListener('submit', function(e) {
  e.preventDefault();
  
  // Correct Answers
  const answerKey = {
    q1: "B",  // 12 characters
    q2: "B",  // Authenticator app
    q3: "B",  // False
    q4: "C"   // Both A and B
  };
  
  // Calculate Score
  let score = 0;
  const userAnswers = {
    q1: document.querySelector('input[name="q1"]:checked')?.value,
    q2: document.querySelector('input[name="q2"]:checked')?.value,
    q3: document.querySelector('input[name="q3"]:checked')?.value,
    q4: document.querySelector('input[name="q4"]:checked')?.value
  };
  
  if (userAnswers.q1 === answerKey.q1) score++;
  if (userAnswers.q2 === answerKey.q2) score++;
  if (userAnswers.q3 === answerKey.q3) score++;
  if (userAnswers.q4 === answerKey.q4) score++;
  
  // Display Results
  const resultsDiv = document.getElementById('quizResults');
  const scoreSpan = document.getElementById('quizScore');
  const feedbackDiv = document.getElementById('quizFeedback');
  const completeAlert = document.getElementById('moduleCompleteAlert');
  const retryAlert = document.getElementById('quizRetryAlert');
  
  scoreSpan.textContent = score;
  resultsDiv.classList.remove('d-none');
  
  // Feedback Messages
  feedbackDiv.innerHTML = `
    <p><strong>Question 1:</strong> 12+ characters are recommended by cybersecurity experts.</p>
    <p><strong>Question 2:</strong> Authenticator apps (like Google Authenticator) are more secure than SMS.</p>
    <p><strong>Question 3:</strong> Never reuse passwords—use a password manager instead.</p>
    <p><strong>Question 4:</strong> Always change passwords AND enable 2FA after breaches.</p>
  `;
  
  // Pass/Fail Logic
  if (score >= 3) {
    completeAlert.classList.remove('d-none');
    retryAlert.classList.add('d-none');
    
    // Mark module complete in backend
    fetch("{{ url_for('update_password_progress') }}", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        quiz_score: score,
        module_completed: true
      })
    }).then(() => {
      // Enable navigation to next module
      document.getElementById('nextModuleBtn').classList.remove('disabled');
    });
    
  } else {
    completeAlert.classList.add('d-none');
    retryAlert.classList.remove('d-none');
  }
});
// Enhanced Quiz Logic
document.getElementById('phishingQuiz').addEventListener('submit', function(e) {
  e.preventDefault();
  
  // Correct Answers
  const answerKey = {
    q1: "A",  // Generic greeting
    q2: "A",  // Yes - suspicious sender
    q3: "B"   // Contact bank directly
  };
  
  // Calculate Score
  let score = 0;
  const userAnswers = {
    q1: document.querySelector('input[name="q1"]:checked')?.value,
    q2: document.querySelector('input[name="q2"]:checked')?.value,
    q3: document.querySelector('input[name="q3"]:checked')?.value
  };
  
  if (userAnswers.q1 === answerKey.q1) score++;
  if (userAnswers.q2 === answerKey.q2) score++;
  if (userAnswers.q3 === answerKey.q3) score++;
  
  // Display Results
  const resultsDiv = document.getElementById('quizResults');
  const scoreSpan = document.getElementById('quizScore');
  const feedbackDiv = document.getElementById('quizFeedback');
  const completionAlert = document.getElementById('completionAlert');
  const retryAlert = document.getElementById('retryAlert');
  
  scoreSpan.textContent = score;
  resultsDiv.classList.remove('d-none');
  
  // Feedback Messages
  feedbackDiv.innerHTML = `
    <p><strong>Question 1:</strong> Generic greetings ("Dear user") are common in phishing.</p>
    <p><strong>Question 2:</strong> Always verify sender addresses (e.g., "amaz0n.com").</p>
    <p><strong>Question 3:</strong> Never click links in unsolicited messages.</p>
  `;
  
  // Pass/Fail Logic
  if (score >= 2) {
    completionAlert.classList.remove('d-none');
    retryAlert.classList.add('d-none');
    
    // Mark module complete
    fetch("{{ url_for('update_phishing_progress') }}", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        score: Math.round((score / 3) * 100),
        is_completed: true
      })
    }).then(() => {
      document.getElementById('nextModuleBtn').classList.remove('disabled');
    });
  } else {
    completionAlert.classList.add('d-none');
    retryAlert.classList.remove('d-none');
  }
});
// Track user classifications
const userClassifications = [];

// Email classification handler
document.querySelectorAll('.classify-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    const card = this.closest('.email-card');
    const isPhishing = card.dataset.isPhishing === 'true';
    const userVerdict = this.dataset.verdict === 'suspicious';
    const emailId = Array.from(document.querySelectorAll('.email-card')).indexOf(card);
    
    // Store user's choice
    userClassifications[emailId] = {
      verdict: userVerdict,
      isCorrect: userVerdict === isPhishing
    };
    
    // Visual feedback
    const feedbackDiv = card.querySelector('.email-feedback');
    feedbackDiv.classList.remove('d-none');
    
    // Disable both buttons after selection
    card.querySelectorAll('.classify-btn').forEach(b => b.disabled = true);
    
    // Immediate feedback
    if (userVerdict === isPhishing) {
      this.classList.remove('btn-outline-danger', 'btn-outline-success');
      this.classList.add(isPhishing ? 'btn-success' : 'btn-danger');
      feedbackDiv.innerHTML = `
        <div class="alert alert-success">
          <i class="bi bi-check-circle me-2"></i>
          <strong>Correct!</strong> ${isPhishing ? 'This is a phishing attempt.' : 'This email is legitimate.'}
        </div>
      `;
    } else {
      this.classList.remove('btn-outline-danger', 'btn-outline-success');
      this.classList.add(isPhishing ? 'btn-success' : 'btn-danger');
      feedbackDiv.innerHTML = `
        <div class="alert alert-danger">
          <i class="bi bi-exclamation-triangle me-2"></i>
          <strong>Incorrect.</strong> ${isPhishing ? 'This was actually phishing!' : 'This email was safe.'}
        </div>
      `;
    }
    
    // Update progress
    updateProgress();
  });
});

// Update progress tracker
function updateProgress() {
  const classifiedCount = userClassifications.filter(Boolean).length;
  const progressText = document.getElementById('progressText');
  const checkBtn = document.getElementById('checkAnswersBtn');
  
  progressText.textContent = `${classifiedCount}/3 emails classified`;
  checkBtn.disabled = classifiedCount < 3;
}

// Final verification
document.getElementById('checkAnswersBtn').addEventListener('click', function() {
  const correctCount = userClassifications.filter(c => c?.isCorrect).length;
  const scorePercent = Math.round((correctCount / 3) * 100);
  
  // Show comprehensive results
  Swal.fire({
    title: `Score: ${correctCount}/3`,
    html: `
      <div class="text-start">
        <p class="${correctCount >= 2 ? 'text-success' : 'text-danger'}">
          <i class="bi bi-${correctCount >= 2 ? 'check' : 'x'}-circle me-2"></i>
          ${correctCount >= 2 ? 'You passed!' : 'Try again (need 2/3 correct)'}
        </p>
        <hr>
        <h6>Key Learnings:</h6>
        <ul>
          <li>Check sender addresses for typos (e.g., micr0soft.com)</li>
          <li>Legitimate companies won't threaten immediate account closure</li>
          <li>Hover over links to preview real URLs</li>
        </ul>
      </div>
    `,
    icon: correctCount >= 2 ? 'success' : 'error',
    confirmButtonText: 'Continue'
  }).then(() => {
    if (correctCount >= 2) {
      // Mark module complete
      fetch("{{ url_for('update_phishing_progress') }}", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          score: scorePercent,
          is_completed: true
        })
      }).then(() => window.location.reload());
    }
  });
});