function updateUrl(params) {
    const url = new URL(window.location.href);
    for (const key in params) {
        url.searchParams.set(key, params[key]);
    }
    window.location.href = url.toString();
};

function normalizeDate(date) {
    if (!date) return;

    const newDate = date.split('-');
    newDate.pop();

    return newDate.join('/');
}

function createSecondaryCard(day) {
    return `
            <div class="card day-card" onclick="updateUrl({ date: '${day?.date || "N/D"}'})">
                <div class="date">${normalizeDate(day?.date) || "N/D"}</div>
                <div class="icon"><i class="ph-duotone ph-cloud-sun icon-weather"></i></div>
                <div class="card-index active-index temperature"><i class="ph-duotone ph-thermometer icon-temp"></i>${day?.temperature || "N/D"}°C</div>
                <div class="card-index humidity"><i class="ph-duotone ph-drop icon-water"></i>${day?.humidity || "N/D"}%</div>
            </div>`;
};

function createMainCard(day) {
    return `
            <div class="card main-card">
                <div>
                <div class="main-date">${normalizeDate(day?.date) || "N/D"}</div>
                <div class="main-temp" id="main-primary">${day?.temperature || "N/D"}°C</div>
                <div class="sub" id="main-secondary">Humidity: ${day?.humidity || "N/D"}%</div>
                <div class="sub">Mean temperature: ${day?.mean_temperature || "N/D"}° C</div>
                </div>
                <div class="main-icon"><i class="ph-duotone ph-cloud-sun icon-weather"></i></div>
            </div>`;
};

const createChartGradient = ((key) => {
    const gradient = ctx.createLinearGradient(0, 230, 0, 50);

    if (key === "temperature") {
        gradient.addColorStop(1, "rgba(75, 192, 192, 0.2)");
        gradient.addColorStop(0.2, "rgba(75, 192, 192, 0.0)");
        gradient.addColorStop(0, "rgba(75, 192, 192, 0)");
    };

    if (key === "humidity") {
        gradient.addColorStop(1, "rgba(54, 162, 235, 0.2)");
        gradient.addColorStop(0.2, "rgba(54, 162, 235, 0.0)");
        gradient.addColorStop(0, "rgba(54, 162, 235, 0)");
    };

    return gradient;
});

const createDataSet = ((key) => {
    return {
        label: tabs[key].label,
        data: tabs[key].data,
        borderColor: tabs[key].border,
        backgroundColor: tabs[key].gradient,
    }
});

// Create cards
const container = document.getElementById('top-container');

if (selected_date_position === "left") {
    // Grid: Primary | Secondary | Secondary
    container.style.gridTemplateColumns = '2fr 1fr 1fr';
    container.innerHTML = createMainCard(current) + createSecondaryCard(next) + createSecondaryCard(next2);
}
if (selected_date_position === "middle") {
    // Grid: Secondary | Primary | Secondary
    container.style.gridTemplateColumns = '1fr 2fr 1fr';
    container.innerHTML = createSecondaryCard(prev) + createMainCard(current) + createSecondaryCard(next);
} else if (selected_date_position === "right") {
    // Grid: Secondary | Secondary | Primary
    container.style.gridTemplateColumns = '1fr 1fr 2fr';
    container.innerHTML = createSecondaryCard(prev2) + createSecondaryCard(prev) + createMainCard(current);
}

// Create Chart
const labels = chart_data.map(item => item.timestamp);
const tempValues = chart_data.map(item => item.temperature);
const humValues = chart_data.map(item => item.humidity);

const ctx = document.getElementById("line-chart-gradient").getContext("2d");

const tabs = {
    temperature: {
        data: tempValues,
        label: "Temperature (°C)",
        gradient: createChartGradient("temperature"),
        border: 'rgba(75,192,192,1)'
    },
    humidity: {
        data: humValues,
        label: "Humidity (%)",
        gradient: createChartGradient("humidity"),
        border: 'rgba(54,162,235,1)'
    }
};

let activeIndex = 'temperature';

const chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: labels,
        datasets: [
            {
                ...createDataSet(activeIndex),
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 3
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            y: { grid: { color: "rgba(200,200,200,0.2)" }, ticks: { color: "#9ca2b7" } },
            x: { ticks: { color: "#9ca2b7" }, grid: { display: false } }
        }
    }
});

// Tablist events
const tablist = document.querySelectorAll('.tablist-item')

for (const tab of tablist) {
    tab.addEventListener('click', () => {
        const key = tab.dataset.tab;
        if (key === activeIndex) return;

        activeIndex = key;

        // Update Chart
        for (const tab of tablist) {
            tab.classList.remove('tablist-active')
        }

        tab.classList.add('tablist-active');

        chart.data.datasets[0] = {
            ...chart.data.datasets[0],
            ...createDataSet(key)
        };
        chart.update();

        // Update Secondary Cards
        document.querySelectorAll('.day-card').forEach(card => {
            const indexes = card.querySelectorAll('.card-index');

            for (let i = 0; i < indexes.length; i++) {
                const index = indexes[i]; index.classList.remove('active-index'); if
                    (index.classList.contains(key)) {
                    index.classList.add('active-index'); // Won't work with > 2 elements
                    card.appendChild(indexes[Math.abs(1 - i)]);
                }
            }
        });

        // Main card
        const primary = document.getElementById('main-primary');
        const secondary = document.getElementById('main-secondary');

        if (key === 'temperature') {
            primary.textContent = `${current.temperature}°C`;
            secondary.textContent = `Humidity: ${current.humidity}%`;
        } else if (key === 'humidity') {
            primary.textContent = `${current.humidity}%`;
            secondary.textContent = `Temperature: ${current.temperature}°C`;
        }
    });
}
