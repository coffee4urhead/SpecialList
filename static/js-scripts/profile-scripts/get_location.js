function getUsernameFromUrl() {
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    if (pathSegments.length >= 2 && pathSegments[0] === 'user') {
        return pathSegments[1];
    }
    console.error('Could not determine username from URL');
    throw new Error('Wasn`t able to extract a proper username!');
}

export function getCookie(name) {
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
            try {
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

                if (!postResponse.ok) {
                    throw new Error('Failed to save location');
                }

                return await postResponse.json();
            } catch (geoError) {
                console.error('Geolocation error:', geoError);
                throw new Error('Could not get your location. Please enable location services.');
            }
        }

        if (!response.ok) {
            throw new Error(data.message || 'Request failed');
        }

        return data;

    } catch (error) {
        console.error('Error fetching combined data:', error);
        return {
            user_location: null,
            connections: {
                followers: [],
                following: []
            }
        };
    }
}

function showErrorToUser(message) {
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    document.body.prepend(errorElement);

    setTimeout(() => {
        errorElement.remove();
    }, 5000);
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

function createProfilePopup(user, relations) {
    return `
        <div class="profile-popup">
            <p>${relations}</p>
            <button class="view-profile filled-web-btn" data-username="${user.username}">
                Message
            </button>
        </div>
    `;
}

function displayAllLocations(userLocation, connections) {
    const mapElement = document.getElementById('map');
    if (mapElement._leaflet_map) {
        mapElement._leaflet_map.remove();
    }

    if (!userLocation || !userLocation.latitude || !userLocation.longitude) {
        showErrorToUser('No location data available to display');
        return;
    }

    const map = L.map('map').setView([userLocation.latitude, userLocation.longitude], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    const createCustomIcon = (profilePicUrl, size = [32, 32]) => {
        return L.divIcon({
            className: 'custom-icon',
            html: `<div style="background-image: url('${profilePicUrl}'); 
                             width: ${size[0]}px; 
                             height: ${size[1]}px;
                             border-radius: 50%;
                             background-size: cover;
                             border: 2px solid white;
                             box-shadow: 0 0 5px rgba(0,0,0,0.3);"></div>`,
            iconSize: size,
            iconAnchor: [size[0] / 2, size[1] / 2],
            popupAnchor: [0, -size[1] / 2]
        });
    };

    const userIcon = createCustomIcon(
        userLocation.profile_picture || '../../static/images/avatar-default-photo.png',
        [40, 40]
    );

    L.marker([userLocation.latitude, userLocation.longitude], {
        icon: userIcon
    })
        .bindPopup(createProfilePopup(userLocation, 'Your location'))
        .on('popupopen', (e) => {
            const popupContent = e.popup.getElement();
            if (popupContent) {
                const button = popupContent.querySelector('.view-profile');
                if (button) {
                    button.addEventListener('click', () => {
                        window.location.href = `/user/${user.username}/`;
                    });
                }
            }
        })
        .addTo(map);

    const processConnections = (users, relationshipType) => {
        users.forEach(user => {
            if (user.latitude && user.longitude) {
                const icon = createCustomIcon(
                    user.profile_picture || '../../static/images/avatar-default-photo.png',
                    [36, 36]
                );

                L.marker([user.latitude, user.longitude], {
                    icon: icon
                }).bindPopup(createProfilePopup(user, relationshipType))
                    .on('popupopen', (e) => {
                        const popupContent = e.popup.getElement();
                        if (popupContent) {
                            const button = popupContent.querySelector('.view-profile');
                            if (button) {
                                button.addEventListener('click', () => {
                                    window.location.href = `/user/${user.username}/`;
                                });
                            }
                        }
                    })
                    .addTo(map);
            }
        });
    };

    processConnections(connections.followers, 'Follower');
    processConnections(connections.following, 'Following');

    setTimeout(() => {
        map.invalidateSize();
        const allLocations = [
            [userLocation.latitude, userLocation.longitude],
            ...connections.followers.map(f => [f.latitude, f.longitude]),
            ...connections.following.map(f => [f.latitude, f.longitude])
        ].filter(loc => loc[0] && loc[1]);

        if (allLocations.length > 0) {
            const bounds = L.latLngBounds([allLocations[0]]);
            allLocations.slice(1).forEach(loc => {
                bounds.extend(loc);
            });

            map.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 15
            });
        }
    }, 100);
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const {user_location, connections} = await getCombinedLocationData();

        if (!user_location) {
            showErrorToUser('Location data not available');
        }

        displayAllLocations(user_location, connections);

    } catch (error) {
        console.error('Failed to load location data:', error);
        showErrorToUser(error.message || 'Failed to load location data');
    }
});