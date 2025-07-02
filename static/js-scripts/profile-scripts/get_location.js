function getUsernameFromUrl() {
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    if (pathSegments.length >= 2 && pathSegments[0] === 'user') {
        return pathSegments[1];
    }
     console.error('Could not determine username from URL');
     throw new Error('Wasn`t able to extract a proper username!');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function getCombinedLocationData() {
    const username = getUsernameFromUrl();

    try {
        const response = await fetch(`/user/${username}/location-with-connections/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.status === 'error' && data.requires_location) {
            const position = await getCurrentPosition();

            const postResponse = await fetch(`/user/${username}/location-with-connections/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                })
            });

            return await postResponse.json();
        }

        if (!response.ok) {
            throw new Error(data.message || 'Request failed');
        }

        return data;

    } catch (error) {
        console.error('Error fetching combined data:', error);
        throw error;
    }
}

function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        });
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const { user_location, connections } = await getCombinedLocationData();

        console.log('User location:', user_location);
        console.log('Connections data:', connections);

        displayAllLocations(user_location, connections);

    } catch (error) {
        console.error('Failed to load location data:', error);
        showErrorToUser('Failed to load location data. Please try again.');
    }
});

function displayAllLocations(userLocation, connections) {
    console.log('Displaying user location:', userLocation);
    console.log('Displaying connections:', connections);
}