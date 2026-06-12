const foodInput = document.getElementById("foodInput");
const caloriesInput = document.getElementById("caloriesInput");
const servingInfo = document.getElementById("servingInfo");
const foodForm = document.getElementById("foodForm");
const foodMessage = document.getElementById("foodMessage");
const planForm = document.getElementById("planForm");
const planMessage = document.getElementById("planMessage");
const planResult = document.getElementById("planResult");
const mealCards = document.getElementById("mealCards");
const targetOutput = document.getElementById("targetOutput");
const recipeForm = document.getElementById("recipeForm");
const recipeMessage = document.getElementById("recipeMessage");
const recipeResult = document.getElementById("recipeResult");
const recipeTitle = document.getElementById("recipeTitle");
const recipeMeta = document.getElementById("recipeMeta");
const recipeIngredients = document.getElementById("recipeIngredients");
const recipeSteps = document.getElementById("recipeSteps");
const recipeSubmitButton = document.getElementById("recipeSubmitButton");
const recipeQuickPicks = document.querySelectorAll(".recipe-quick-picks button");
const bmiForm = document.getElementById("bmiForm");
const bmiMessage = document.getElementById("bmiMessage");
const bmiResult = document.getElementById("bmiResult");
const bmiValue = document.getElementById("bmiValue");
const bmiCategory = document.getElementById("bmiCategory");
const bmiAdvice = document.getElementById("bmiAdvice");
const themeToggle = document.getElementById("themeToggle");
const moonIcon = document.querySelector(".theme-icon-moon");
const sunIcon = document.querySelector(".theme-icon-sun");
const signupForm = document.getElementById("signupForm");
const loginForm = document.getElementById("loginForm");
const showLoginButton = document.getElementById("showLogin");
const showSignupButton = document.getElementById("showSignup");
const authTitle = document.getElementById("authTitle");
const authSubtitle = document.getElementById("authSubtitle");
const logoutButton = document.getElementById("logoutButton");
const authMessage = document.getElementById("authMessage");
const analyticsDataElement = document.getElementById("analyticsData");
const todayCaloriesChart = document.getElementById("todayCaloriesChart");
const topFoodsChart = document.getElementById("topFoodsChart");

function applyTheme(theme) {
    const darkModeEnabled = theme === "dark";
    document.body.classList.toggle("dark-mode", darkModeEnabled);
    if (themeToggle) {
        themeToggle.setAttribute(
            "aria-label",
            darkModeEnabled ? "Switch to light mode" : "Switch to dark mode"
        );
    }
    if (moonIcon) {
        moonIcon.classList.toggle("hidden", darkModeEnabled);
    }
    if (sunIcon) {
        sunIcon.classList.toggle("hidden", !darkModeEnabled);
    }
    drawAnalyticsCharts();
}

function getAnalyticsData() {
    if (!analyticsDataElement) {
        return null;
    }

    try {
        return JSON.parse(analyticsDataElement.textContent);
    } catch (error) {
        return null;
    }
}

function setupCanvas(canvas) {
    if (!canvas) {
        return null;
    }

    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 400;
    const height = canvas.clientHeight || 220;
    canvas.width = width * ratio;
    canvas.height = height * ratio;

    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { ctx, width, height };
}

function drawRoundedRect(ctx, x, y, width, height, radius) {
    const safeRadius = Math.min(radius, width / 2, height / 2);
    ctx.beginPath();
    ctx.moveTo(x + safeRadius, y);
    ctx.lineTo(x + width - safeRadius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + safeRadius);
    ctx.lineTo(x + width, y + height - safeRadius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - safeRadius, y + height);
    ctx.lineTo(x + safeRadius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - safeRadius);
    ctx.lineTo(x, y + safeRadius);
    ctx.quadraticCurveTo(x, y, x + safeRadius, y);
    ctx.closePath();
}

function drawEmptyChart(canvas, message) {
    const setup = setupCanvas(canvas);
    if (!setup) {
        return;
    }

    const { ctx, width, height } = setup;
    const isDark = document.body.classList.contains("dark-mode");
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = isDark ? "#b2beb6" : "#675f57";
    ctx.font = "14px DM Sans, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(message, width / 2, height / 2);
}

function drawBarChart(canvas, labels, values, color) {
    const setup = setupCanvas(canvas);
    if (!setup) {
        return;
    }

    const { ctx, width, height } = setup;
    const isDark = document.body.classList.contains("dark-mode");
    const textColor = isDark ? "#eef3ef" : "#1d1a17";
    const mutedColor = isDark ? "#b2beb6" : "#675f57";
    const lineColor = isDark ? "rgba(255,255,255,0.12)" : "rgba(29,26,23,0.12)";
    if (!labels.length) {
        drawEmptyChart(canvas, "No calories logged today yet.");
        return;
    }

    const maxValue = Math.max(...values, 1);
    const padding = { top: 18, right: 16, bottom: 42, left: 16 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const step = chartWidth / values.length;
    const barWidth = Math.min(44, step * 0.58);

    ctx.clearRect(0, 0, width, height);
    ctx.font = "12px DM Sans, sans-serif";

    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 1;
    for (let i = 0; i < 4; i += 1) {
        const y = padding.top + (chartHeight / 3) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
    }

    values.forEach((value, index) => {
        const x = padding.left + step * index + (step - barWidth) / 2;
        const barHeight = (value / maxValue) * (chartHeight - 8);
        const y = padding.top + chartHeight - barHeight;

        ctx.fillStyle = color;
        drawRoundedRect(ctx, x, y, barWidth, Math.max(barHeight, 6), 10);
        ctx.fill();

        ctx.fillStyle = textColor;
        ctx.textAlign = "center";
        ctx.fillText(String(value), x + barWidth / 2, y - 8);

        ctx.fillStyle = mutedColor;
        ctx.fillText(labels[index], x + barWidth / 2, height - 14);
    });
}

function drawHorizontalChart(canvas, items) {
    const setup = setupCanvas(canvas);
    if (!setup || !items.length) {
        if (canvas) {
            drawEmptyChart(canvas, "No food data yet.");
        }
        return;
    }

    const { ctx, width, height } = setup;
    const isDark = document.body.classList.contains("dark-mode");
    const textColor = isDark ? "#eef3ef" : "#1d1a17";
    const mutedColor = isDark ? "#b2beb6" : "#675f57";
    const trackColor = isDark ? "rgba(255,255,255,0.09)" : "rgba(29,26,23,0.08)";
    const palette = ["#d96c3d", "#1f8f5f", "#f3b340", "#5a7cff", "#b85ad6"];
    const maxValue = Math.max(...items.map((item) => item.total_calories), 1);
    const startX = 120;
    const barMaxWidth = width - startX - 24;
    const rowHeight = 34;
    const top = 24;

    ctx.clearRect(0, 0, width, height);
    ctx.font = "12px DM Sans, sans-serif";

    items.forEach((item, index) => {
        const y = top + index * rowHeight;
        const barWidth = (item.total_calories / maxValue) * barMaxWidth;

        ctx.fillStyle = textColor;
        ctx.textAlign = "left";
        ctx.fillText(item.food.slice(0, 16), 12, y + 12);

        ctx.fillStyle = trackColor;
        drawRoundedRect(ctx, startX, y, barMaxWidth, 12, 8);
        ctx.fill();

        ctx.fillStyle = palette[index % palette.length];
        drawRoundedRect(ctx, startX, y, Math.max(barWidth, 10), 12, 8);
        ctx.fill();

        ctx.fillStyle = mutedColor;
        ctx.fillText(`${item.total_calories} cal`, startX, y + 27);
    });
}

function drawAnalyticsCharts() {
    const analytics = getAnalyticsData();
    if (!analytics) {
        return;
    }

    if (todayCaloriesChart) {
        const todayFoods = analytics.today_foods || [];
        const labels = todayFoods.map((item) =>
            item.entries > 1 ? `${item.food} x${item.entries}` : item.food
        );
        const values = todayFoods.map((item) => item.total_calories);
        drawBarChart(todayCaloriesChart, labels, values, "#d96c3d");
    }

    if (topFoodsChart) {
        drawHorizontalChart(topFoodsChart, analytics.top_foods);
    }
}

const savedTheme = localStorage.getItem("theme") || "light";
if (themeToggle) {
    applyTheme(savedTheme);

    themeToggle.addEventListener("click", () => {
        const nextTheme = document.body.classList.contains("dark-mode") ? "light" : "dark";
        localStorage.setItem("theme", nextTheme);
        applyTheme(nextTheme);
    });
}

if (!themeToggle) {
    drawAnalyticsCharts();
}

window.addEventListener("resize", drawAnalyticsCharts);

function showAuthError(data, fallbackElement) {
    if (data && data.error === "Please login first.") {
        if (authMessage) {
            authMessage.textContent = data.error;
        }
        if (fallbackElement) {
            fallbackElement.textContent = data.error;
        }
        return true;
    }
    return false;
}

function setAuthMode(mode) {
    const showingSignup = mode === "signup";
    if (loginForm) {
        loginForm.classList.toggle("hidden", showingSignup);
    }
    if (signupForm) {
        signupForm.classList.toggle("hidden", !showingSignup);
    }
    if (showLoginButton) {
        showLoginButton.classList.toggle("active", !showingSignup);
        showLoginButton.setAttribute("aria-pressed", String(!showingSignup));
    }
    if (showSignupButton) {
        showSignupButton.classList.toggle("active", showingSignup);
        showSignupButton.setAttribute("aria-pressed", String(showingSignup));
    }
    if (authTitle) {
        authTitle.textContent = showingSignup ? "Sign Up" : "Login";
    }
    if (authSubtitle) {
        authSubtitle.textContent = showingSignup
            ? "New here? Create your account to start using MealMetric."
            : "Welcome back. Enter your details to continue.";
    }
    if (authMessage) {
        authMessage.textContent = "";
    }
}

if (showLoginButton) {
    showLoginButton.addEventListener("click", () => setAuthMode("login"));
}

if (showSignupButton) {
    showSignupButton.addEventListener("click", () => setAuthMode("signup"));
}

if (showLoginButton || showSignupButton) {
    setAuthMode("login");
}

if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const response = await fetch("/signup", {
            method: "POST",
            body: new FormData(signupForm),
        });

        const data = await response.json();
        authMessage.textContent = data.message || data.error || "";

        if (response.ok) {
            window.location.reload();
        }
    });
}

if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const response = await fetch("/login", {
            method: "POST",
            body: new FormData(loginForm),
        });

        const data = await response.json();
        authMessage.textContent = data.message || data.error || "";

        if (response.ok) {
            window.location.reload();
        }
    });
}

if (logoutButton) {
    logoutButton.addEventListener("click", async () => {
        const response = await fetch("/logout", {
            method: "POST",
        });

        const data = await response.json();
        if (authMessage) {
            authMessage.textContent = data.message || "";
        }

        if (response.ok) {
            window.location.reload();
        }
    });
}

async function fetchCalories(foodName) {
    if (!foodName.trim()) {
        caloriesInput.value = "";
        servingInfo.value = "";
        return;
    }

    const response = await fetch(`/get_calories?food_name=${encodeURIComponent(foodName)}`);
    const data = await response.json();

    caloriesInput.value = data.calories || "";
    servingInfo.value = data.serving || "Serving not found";
}

if (foodInput) {
    foodInput.addEventListener("change", () => fetchCalories(foodInput.value));
    foodInput.addEventListener("blur", () => fetchCalories(foodInput.value));
}

if (foodForm) {
    foodForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(foodForm);
        const response = await fetch("/add", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();
        if (showAuthError(data, foodMessage)) {
            return;
        }

        if (!response.ok) {
            foodMessage.textContent = data.error || "Unable to add food.";
            return;
        }

        foodMessage.textContent = data.message;
        window.location.reload();
    });
}

async function deleteItem(itemId) {
    const response = await fetch(`/delete/${itemId}`, {
        method: "POST",
    });

    if (response.ok) {
        window.location.reload();
        return;
    }

    const data = await response.json();
    showAuthError(data, authMessage);
    if (authMessage && data.error) {
        authMessage.textContent = data.error;
    }
}

if (planForm) {
    planForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const payload = {
            age: document.getElementById("age").value,
            weight: document.getElementById("weight").value,
            height: document.getElementById("height").value,
            gender: document.getElementById("gender").value,
            activity: document.getElementById("activity").value,
            goal: document.getElementById("goal").value,
        };

        const response = await fetch("/plan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (showAuthError(data, planMessage)) {
            planResult.classList.add("hidden");
            return;
        }

        if (!response.ok) {
            planMessage.textContent = data.error || "Unable to generate plan.";
            planResult.classList.add("hidden");
            return;
        }

        planMessage.textContent = data.advice || `Plan generated for ${data.goal} goal.`;
        targetOutput.textContent = data.target_calories;
        mealCards.innerHTML = data.meals
            .map(
                (meal) => `
                    <article class="meal-card">
                        <h5>${meal.meal}</h5>
                        <p><strong>Target:</strong> ${meal.target} cal</p>
                        <p><strong>Total:</strong> ${meal.calories} cal</p>
                        <ul class="recipe-list meal-item-list">
                            ${(meal.items || [])
                                .map(
                                    (item) => `
                                        <li>
                                            ${item.food} - ${item.portions > 1 ? `${item.portions} x ` : ""}${item.serving}
                                            <span>${item.total_calories} cal</span>
                                        </li>
                                    `
                                )
                                .join("")}
                        </ul>
                        <p><strong>Balance:</strong> ${
                            meal.gap === 0
                                ? "On target"
                                : `${Math.abs(meal.gap)} cal ${meal.gap > 0 ? "over" : "under"}`
                        }</p>
                    </article>
                `
            )
            .join("");

        planResult.classList.remove("hidden");
    });
}

if (recipeForm) {
    recipeQuickPicks.forEach((button) => {
        button.addEventListener("click", () => {
            const ingredient = button.dataset.ingredient || "";
            const recipeIngredient = document.getElementById("recipeIngredient");
            if (recipeIngredient) {
                recipeIngredient.value = ingredient;
                recipeIngredient.focus();
            }
        });
    });

    recipeForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const ingredient = document.getElementById("recipeIngredient").value.trim();
        if (!ingredient) {
            recipeMessage.textContent = "Please enter a main ingredient.";
            recipeResult.classList.add("hidden");
            return;
        }

        const payload = {
            ingredient,
            meal_type: document.getElementById("recipeMealType").value,
            goal: document.getElementById("recipeGoal").value,
        };

        recipeMessage.textContent = "Generating recipe...";
        recipeResult.classList.add("hidden");
        if (recipeSubmitButton) {
            recipeSubmitButton.disabled = true;
            recipeSubmitButton.textContent = "Generating...";
        }

        let response;
        let data;
        try {
            response = await fetch("/recipe", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });
            data = await response.json();
        } catch (error) {
            recipeMessage.textContent = "Unable to generate recipe right now. Please try again.";
            return;
        } finally {
            if (recipeSubmitButton) {
                recipeSubmitButton.disabled = false;
                recipeSubmitButton.textContent = "Generate Recipe";
            }
        }

        if (showAuthError(data, recipeMessage)) {
            recipeResult.classList.add("hidden");
            return;
        }

        if (!response.ok) {
            recipeMessage.textContent = data.error || "Unable to generate recipe.";
            recipeResult.classList.add("hidden");
            return;
        }

        recipeMessage.textContent = data.summary || `Recipe generated for ${data.goal} goal.`;
        recipeTitle.textContent = data.name;
        recipeMeta.textContent = `${data.meal_type} | ${data.estimated_calories} cal | ${data.prep_time} | ${data.tip}`;
        recipeIngredients.innerHTML = `
            <ul class="recipe-list">
                ${data.ingredients
                    .map(
                        (item) =>
                            `<li>${item.food} - ${item.serving} - ${item.calories} cal <span>${item.category}</span></li>`
                    )
                    .join("")}
            </ul>
        `;
        recipeSteps.innerHTML = `
            <ol class="recipe-list">
                ${data.steps.map((step) => `<li>${step}</li>`).join("")}
            </ol>
        `;

        recipeResult.classList.remove("hidden");
    });
}

if (bmiForm) {
    bmiForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const payload = {
            weight: document.getElementById("bmiWeight").value,
            height: document.getElementById("bmiHeight").value,
        };

        const response = await fetch("/bmi", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (showAuthError(data, bmiMessage)) {
            bmiResult.classList.add("hidden");
            return;
        }

        if (!response.ok) {
            bmiMessage.textContent = data.error || "Unable to calculate BMI.";
            bmiResult.classList.add("hidden");
            return;
        }

        bmiMessage.textContent = "BMI calculated successfully.";
        bmiValue.textContent = data.bmi;
        bmiCategory.textContent = data.category;
        bmiAdvice.textContent = data.advice;
        bmiResult.classList.remove("hidden");
    });
}
