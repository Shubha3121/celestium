// YOUR API KEY (Get one at https://api.nasa.gov/ for higher limits, or use DEMO_KEY)
const NASA_API_KEY = 'waXwp40nut4BeweNhRnKSnLQkydLO3fAC1KWqsfY'; 
const NASA_BASE_URL = 'https://api.nasa.gov';



export const SpaceData = {
    // NEW: Fetch the last 6 days of space topics
    async getRecentDiscoveries() {
        try {
            // Calculate dates
            const today = new Date();
            const lastWeek = new Date();
            lastWeek.setDate(today.getDate() - 6); // Go back 6 days

            // Format dates as YYYY-MM-DD
            const formatDate = (date) => date.toISOString().split('T')[0];
            const startDate = formatDate(lastWeek);
            const endDate = formatDate(today);

            const response = await fetch(`${NASA_BASE_URL}/planetary/apod?api_key=${NASA_API_KEY}&start_date=${startDate}&end_date=${endDate}`);
            const data = await response.json();
            
            // Reverse so the newest is first
            return data.reverse(); 
        } catch (error) {
            console.error("Failed to fetch discoveries:", error);
            return [];
        }
    }
};