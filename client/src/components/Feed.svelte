<script>
    import { onMount, onDestroy } from "svelte";
    import * as timeago from "timeago.js";
    import anchorme from "anchorme";
    import { createAvatar } from "@dicebear/avatars";
    import * as style from "@dicebear/avatars-bottts-sprites";

    let hostAccessKey = "";
    let newPost;
    let friendFeedLoaded = false;
    let friendFeedPosts;
    let friendListResp;
    let friendListLoaded = false;
    let myKeyLoaded = false;
    let notifications;
    let hostBridge = window.location.hostname;
    let devBridge = "";
    let notifyBridge;
    let refreshingFeed = false;
    let hostUsername;
    let postOptions = false;
    let postOptionSelector;
    let reactToPost = false;
    let reactingPost;
    let lastUpdate;
    let feedLength = 50;
    let hostSeed;

    if (hostBridge == "localhost") {
        devBridge = "https://41034m.deta.dev/";
    }

    onMount(async () => {
        getMyKey();
        quickFeed();
        getFriends();
        getMyName();
    });

    onDestroy(async () => {
        clearInterval(getNotifications);
    });

    const getMyName = async () => {
        var myNameReq = await fetch(devBridge + "public/profile");
        var myNameResp = await myNameReq.json();
        hostUsername = myNameResp.username;
        hostSeed = myNameResp.seed;
    };

    const getMyKey = async () => {
        var myKeyReq = await fetch(devBridge + "my-key?");
        var myKeyResp = await myKeyReq.json();
        hostAccessKey = myKeyResp.key;
        myKeyLoaded = true;
    };

    const createPost = async () => {
        // Only required for Dev - TODO: Remove Jank
        if (window.location.hostname == "localhost") {
            var postBridge = "41034m.deta.dev";
        } else {
            var postBridge = hostBridge;
        }

        if (anchorme.validate.url(newPost)) {
            createLinkPost();
            return;
        }

        if (newPost.length > 2500) {
            alert(
                `Post too long! ${newPost.length} characters, max accepted is 2500`
            );
            return;
        }

        var postedPost = newPost;
        newPost = "";
        refreshingFeed = true;
        var contentToPost = {
            access_key: hostAccessKey,
            value: postedPost,
            bridge: postBridge,
        };

        var postResp = await fetch(devBridge + "create-post", {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(contentToPost),
        });

        await getFeed();
        await notifyFriends();
    };

    const createLinkPost = async () => {
        if (newPost.startsWith("http://") || newPost.startsWith("https://")) {
        } else {
            newPost = "https://" + newPost;
        }

        if (
            newPost.endsWith(".gif") ||
            newPost.endsWith(".jpg") ||
            newPost.endsWith(".png")
        ) {
            var postedPost = `<a href="${newPost}"><img src="${newPost}"></a>`;
        } else {
            var metaFetch = await fetch(devBridge + "metatags?link=" + newPost);
            var metaTags = await metaFetch.json();
            var titleLink = metaTags.title.link(newPost);
            var description;

            if (metaTags.image != "None") {
                var image = `<a href="${newPost}"><img src="${metaTags.image}"></a>`;
            } else {
                var image = "";
            }

            if (metaTags.description != "None") {
                description = metaTags.description;
            } else {
                description = " ";
            }

            var postedPost = `<b>${titleLink}</b><br><br>${image}<br>${description}`;
        }

        // Only required for Dev - TODO: Remove Jank
        if (window.location.hostname == "localhost") {
            var postBridge = "41034m.deta.dev";
        } else {
            var postBridge = hostBridge;
        }

        newPost = "";
        refreshingFeed = true;
        var contentToPost = {
            access_key: hostAccessKey,
            value: postedPost,
            bridge: postBridge,
        };

        var postResp = await fetch(devBridge + "create-post", {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(contentToPost),
        });

        await getFeed();
        await notifyFriends();
    };

    const getFeed = async () => {
        refreshingFeed = true;
        var FeedReq = await fetch(
            devBridge +
                "feed?" +
                new URLSearchParams({
                    access_key: hostAccessKey,
                    cache: "true",
                })
        );
        friendFeedPosts = await FeedReq.json();

        // Add Index
        friendFeedPosts = friendFeedPosts.map((item, index) => ({
            index,
            ...item,
        }));

        friendFeedLoaded = true;
        refreshingFeed = false;
    };

    const quickFeed = async () => {
        var FeedReq = await fetch(
            devBridge +
                "feed?" +
                new URLSearchParams({
                    access_key: hostAccessKey,
                    cached: "true",
                })
        );
        friendFeedPosts = await FeedReq.json();

        // Add Index
        friendFeedPosts = friendFeedPosts.map((item, index) => ({
            index,
            ...item,
        }));

        friendFeedLoaded = true;
    };

    const notifyFriends = async () => {
        friendListResp.forEach(async (friend) => {
            // Only required for Dev - TODO: Remove Jank
            if (window.location.hostname == "localhost") {
                notifyBridge = "41034m.deta.dev";
            } else {
                notifyBridge = hostBridge;
            }

            var contentToPost = {
                key: hostAccessKey,
                bridge: notifyBridge,
            };
            var friendNotifURL = `https://${friend.bridge}/public/notify`;
            var notifyResp = await fetch(friendNotifURL, {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(contentToPost),
            });
        });
    };

    const getFriends = async () => {
        var listReq = await fetch(
            devBridge +
                "friend-list?" +
                new URLSearchParams({
                    access_key: hostAccessKey,
                })
        );
        friendListResp = await listReq.json();
        friendListLoaded = true;
    };

    function friendNameFromBridge(bridge) {
        if (bridge == hostBridge) {
            return hostUsername;
        }

        var filtered = friendListResp;

        filtered.filter(function (friend) {
            if (friend.bridge == bridge) {
                return true;
            }
        });

        try {
            return filtered[0].name;
        } catch (e) {
            return "";
        }
    }

    function convertTimestamp(timestamp) {
        var dateObject = new Date(timestamp * 1000);
        var readableDate = dateObject.toLocaleString();
        return readableDate;
    }

    const clearNotifications = async () => {
        await fetch(
            devBridge +
                "notifications" +
                new URLSearchParams({
                    clear: "True",
                })
        );
    };

    const checkNotifications = async () => {
        if (friendFeedLoaded && friendListLoaded) {
            var notificationsReq = await fetch(devBridge + "notifications");
            notifications = await notificationsReq.json();

            if (notifications.notifications !== "No Notifications") {
                getFeed();
                clearNotifications();
                lastUpdate = notifications.updated;
            }

            if (lastUpdate == null) {
                lastUpdate = notifications.updated;
            }

            if (lastUpdate < notifications.updated) {
                getFeed();
                lastUpdate = notifications.updated;
            }
        }
    };

    const editPost = async (key, updatedContent) => {
        var contentToEdit = {
            item: "post",
            delete: false,
            key: key,
            content: updatedContent,
        };

        var editResp = await fetch(devBridge + "edit", {
            method: "PUT",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(contentToEdit),
        });

        getFeed();
        notifyFriends();
    };

    const deletePost = async (key) => {
        var contentToDelete = {
            item: "post",
            delete: true,
            key: key,
        };

        var deleteResp = await fetch(devBridge + "edit", {
            method: "PUT",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(contentToDelete),
        });

        getFeed();
        notifyFriends();
    };

    const reactPost = async (key, reacted, bridge) => {
        var reactionToPost = {
            postkey: key,
            emoji: reacted,
            bridge: hostBridge,
        };

        var reactResp = await fetch(`https://${bridge}/public/react`, {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(reactionToPost),
        });
        getFeed();
        notifyFriends();
    };

    const reactionList = ["❤️", "🔥", "🤬", "😂", "👎", "👍"];

    const genAvatar = (value) => {
        var avatar = createAvatar(style, {
            seed: value,
        });
        return avatar;
    };

    // Intervals
    const getNotifications = setInterval(checkNotifications, 1000);
</script>

<div class="container w-full p-2 mx-auto sm:p-10 md:w-2/3 lg:w-1/2 xl:w-1/2">
    <div
        class="p-2 mb-2 bg-gray-100 border-2 border-gray-200 rounded shadow-md dark:bg-truegray-800 dark:border-truegray-900"
    >
        <textarea
            placeholder="Post something?..."
            bind:value={newPost}
            class="w-full p-1 border rounded shadow focus:outline-none dark:text-gray-300 dark:bg-truegray-900 dark:border-gray-900"
            rows="3"
        />
        <div class="flex">
            <div class="mt-2 mb-2 ml-auto">
                {#if newPost}
                    <button
                        title="Create Post"
                        on:click={createPost}
                        class="p-2 text-white bg-blue-500 border hover:bg-blue-400 rounded-3xl focus:outline-none dark:bg-truegray-700 dark:hover:bg-truegray-600 dark:border-truegray-600"
                        ><svg
                            class="w-6 h-6"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                            xmlns="http://www.w3.org/2000/svg"
                            ><path
                                fill-rule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clip-rule="evenodd"
                            /></svg
                        ></button
                    >{:else}
                    <button
                        title="Create Post"
                        on:click={() => {
                            alert("Nothing to post...");
                        }}
                        class="p-2 text-white bg-gray-300 border rounded-3xl focus:outline-none dark:bg-truegray-900 dark:border-truegray-700"
                        ><svg
                            class="w-6 h-6 dark:text-truegray-600"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                            xmlns="http://www.w3.org/2000/svg"
                            ><path
                                fill-rule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clip-rule="evenodd"
                            /></svg
                        ></button
                    >
                {/if}
            </div>
        </div>
    </div>

    <div class="pt-2">
        {#if friendFeedLoaded}
            {#if refreshingFeed}
                <div
                    class="flex justify-center text-center text-gray-600 align-middle"
                >
                    <svg
                        class="w-6 h-6 m-2 animate-bounce"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                        xmlns="http://www.w3.org/2000/svg"
                        ><path
                            fill-rule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z"
                            clip-rule="evenodd"
                        /></svg
                    >
                </div>
            {/if}

            {#if friendFeedLoaded && !refreshingFeed && friendFeedPosts.length < 1}
                <div
                    class="flex items-center justify-center p-8 my-6 bg-gray-200 shadow-md hover:shodow-lg rounded-2xl dark:bg-truegray-800"
                >
                    <div class="flex items-center">
                        <svg
                            class="w-20 h-20 text-purple-700 animate-pulse"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                            xmlns="http://www.w3.org/2000/svg"
                            ><path
                                fill-rule="evenodd"
                                d="M9.504 1.132a1 1 0 01.992 0l1.75 1a1 1 0 11-.992 1.736L10 3.152l-1.254.716a1 1 0 11-.992-1.736l1.75-1zM5.618 4.504a1 1 0 01-.372 1.364L5.016 6l.23.132a1 1 0 11-.992 1.736L4 7.723V8a1 1 0 01-2 0V6a.996.996 0 01.52-.878l1.734-.99a1 1 0 011.364.372zm8.764 0a1 1 0 011.364-.372l1.733.99A1.002 1.002 0 0118 6v2a1 1 0 11-2 0v-.277l-.254.145a1 1 0 11-.992-1.736l.23-.132-.23-.132a1 1 0 01-.372-1.364zm-7 4a1 1 0 011.364-.372L10 8.848l1.254-.716a1 1 0 11.992 1.736L11 10.58V12a1 1 0 11-2 0v-1.42l-1.246-.712a1 1 0 01-.372-1.364zM3 11a1 1 0 011 1v1.42l1.246.712a1 1 0 11-.992 1.736l-1.75-1A1 1 0 012 14v-2a1 1 0 011-1zm14 0a1 1 0 011 1v2a1 1 0 01-.504.868l-1.75 1a1 1 0 11-.992-1.736L16 13.42V12a1 1 0 011-1zm-9.618 5.504a1 1 0 011.364-.372l.254.145V16a1 1 0 112 0v.277l.254-.145a1 1 0 11.992 1.736l-1.735.992a.995.995 0 01-1.022 0l-1.735-.992a1 1 0 01-.372-1.364z"
                                clip-rule="evenodd"
                            /></svg
                        >
                    </div>
                    <div class="flex flex-col ml-3">
                        <div class="font-medium leading-none">
                            You Don't Have Any Posts Just Yet!
                        </div>
                        <p
                            class="mt-1 text-sm leading-none text-gray-600 dark:text-truegray-300"
                        >
                            When you post things here your friends will be able
                            to see them in their live feed, or be able to check
                            them out on your profile. You can post basic text or
                            even links that will be embedded in the feed. You
                            can even link directly to some types of images. You
                            can respond to your friends posts with emojis and if
                            you are the creator of a post you'll also be able to
                            edit or delete it.
                        </p>
                    </div>
                </div>
            {/if}

            {#each friendFeedPosts as { name, value, time, edited, key, reactions, bridge, index }}
                {#if index < feedLength}
                    <div class="p-1">
                        <div
                            class="p-4 bg-gray-100 border-2 rounded-lg shadow-lg dark:bg-truegray-800 dark:border-truegray-900"
                        >
                            <div class="flex">
                                <div
                                    class="w-12 h-12 p-2 mr-2 rounded-full bg-truegray-300 dark:bg-truegray-900"
                                >
                                    {@html genAvatar(name)}
                                </div>
                                <div>
                                    {#if name == hostUsername}
                                        <p class="font-medium text-purple-600">
                                            {name}
                                            <span title="Host">
                                                <svg
                                                    class="inline-block w-4 h-4 mb-1 text-green-300 dark:text-green-500"
                                                    fill="currentColor"
                                                    viewBox="0 0 20 20"
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    ><path
                                                        fill-rule="evenodd"
                                                        d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                                        clip-rule="evenodd"
                                                    /></svg
                                                >
                                            </span>
                                            {#if edited == true}
                                                <span title="Edited">
                                                    <svg
                                                        xmlns="http://www.w3.org/2000/svg"
                                                        class="inline-block w-4 h-4 mb-1 text-blue-300"
                                                        fill="none"
                                                        viewBox="0 0 24 24"
                                                        stroke="currentColor"
                                                    >
                                                        <path
                                                            stroke-linecap="round"
                                                            stroke-linejoin="round"
                                                            stroke-width="2"
                                                            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                                        />
                                                    </svg>
                                                </span>
                                            {/if}
                                        </p>
                                    {:else}
                                        <p class="font-medium text-indigo-600">
                                            {name}
                                            {#if edited == true}
                                                <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    class="inline-block w-4 h-4 mb-1 text-blue-300"
                                                    fill="none"
                                                    viewBox="0 0 24 24"
                                                    stroke="currentColor"
                                                >
                                                    <path
                                                        stroke-linecap="round"
                                                        stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                                    />
                                                </svg>
                                            {/if}
                                        </p>
                                    {/if}

                                    <div
                                        class="flex items-center text-xs text-gray-400"
                                    >
                                        <p>
                                            {convertTimestamp(time)}
                                        </p>
                                        <p class="px-1">•</p>
                                        <p>
                                            {timeago.format(
                                                convertTimestamp(time)
                                            )}
                                        </p>
                                    </div>
                                </div>
                                {#if name == hostUsername}
                                    <button
                                        class="ml-auto focus:outline-none"
                                        on:click={() => {
                                            if (postOptionSelector == key) {
                                                postOptions = !postOptions;
                                            } else {
                                                postOptions = true;
                                            }
                                            postOptionSelector = key;

                                            if (reactingPost == key) {
                                                reactToPost = !reactToPost;
                                            } else {
                                                reactToPost = true;
                                            }
                                            reactingPost = key;
                                        }}
                                    >
                                        <svg
                                            class="w-6 h-6 text-gray-300 dark:text-truegray-700"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                            xmlns="http://www.w3.org/2000/svg"
                                            ><path
                                                d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
                                            /></svg
                                        >
                                    </button>
                                {:else}
                                    <button
                                        class="ml-auto focus:outline-none"
                                        on:click={() => {
                                            if (reactingPost == key) {
                                                reactToPost = !reactToPost;
                                            } else {
                                                reactToPost = true;
                                            }
                                            reactingPost = key;
                                        }}
                                    >
                                        <svg
                                            class="w-6 h-6 text-gray-300 dark:text-truegray-700"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                            xmlns="http://www.w3.org/2000/svg"
                                            ><path
                                                d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
                                            /></svg
                                        >
                                    </button>
                                {/if}
                            </div>

                            <div class="mt-2">
                                <p
                                    class="text-sm text-gray-600 break-words line-clamp-3 dark:text-truegray-300"
                                >
                                    {@html anchorme(value)}
                                </p>
                                <div class="flex mt-2">
                                    {#if name == hostUsername && postOptions == true && postOptionSelector == key}
                                        <button
                                            on:click={async () => {
                                                var updatedContent = prompt(
                                                    "Edit Post",
                                                    value
                                                );
                                                if (updatedContent) {
                                                    editPost(
                                                        key,
                                                        updatedContent
                                                    );
                                                    postOptions = false;
                                                    reactToPost = false;
                                                }
                                            }}
                                            class="flex items-center mr-2 text-yellow-400 md:mr-4 focus:outline-none hover:text-yellow-500"
                                        >
                                            <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                class="w-4 h-4 mr-1"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                            >
                                                <path
                                                    stroke-linecap="round"
                                                    stroke-linejoin="round"
                                                    stroke-width="2"
                                                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                                                />
                                            </svg>

                                            <span class="mt-1 text-sm">
                                                Edit
                                            </span>
                                        </button>

                                        <button
                                            on:click={async () => {
                                                if (
                                                    confirm(
                                                        "Are you sure you want to delete this post?"
                                                    )
                                                ) {
                                                    deletePost(key);
                                                    postOptions = false;
                                                    reactToPost = false;
                                                }
                                            }}
                                            class="flex items-center mr-2 text-red-300 md:mr-4 focus:outline-none hover:text-red-400 dark:hover:text-red-700 dark:text-red-600"
                                        >
                                            <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                class="w-4 h-4 mr-1"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                            >
                                                <path
                                                    stroke-linecap="round"
                                                    stroke-linejoin="round"
                                                    stroke-width="2"
                                                    d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                                                />
                                            </svg>

                                            <span
                                                class="mt-1 text-sm focus:outline-none"
                                            >
                                                Delete
                                            </span>
                                        </button>
                                    {/if}
                                    <div class="flex ml-auto">
                                        {#if reactToPost == true && reactingPost == key}
                                            <div class="flex justify-end">
                                                {#each reactionList as displayedReaction}
                                                    <button
                                                        class="ml-1 mr-1 focus:outline-none"
                                                        on:click={async () => {
                                                            postOptions = false;
                                                            var reacted =
                                                                displayedReaction;
                                                            reactToPost = false;
                                                            reactPost(
                                                                key,
                                                                reacted,
                                                                bridge
                                                            );
                                                        }}
                                                        >{displayedReaction}</button
                                                    >
                                                {/each}
                                            </div>
                                        {/if}
                                    </div>
                                </div>
                                {#if reactions.length != 0 && friendListResp}
                                    <div
                                        class="flex flex-shrink pl-2 pr-2 mt-2 -mb-3 bg-purple-900 border border-purple-800 cursor-default rounded-2xl w-min"
                                    >
                                        {#each reactions as { emoji, reacting }}
                                            <span
                                                title={friendNameFromBridge(
                                                    reacting
                                                )}
                                                class="ml-1 mr-1">{emoji}</span
                                            >
                                        {/each}
                                    </div>
                                {/if}
                            </div>
                        </div>
                    </div>
                {/if}
            {/each}
            {#if feedLength < friendFeedPosts.length}
                <div class="flex items-center justify-center py-4">
                    <div
                        class="px-3 py-2 text-purple-200 bg-purple-600 border-2 border-purple-500 rounded-lg cursor-pointer hover:bg-purple-700 hover:border-purple-600 hover:text-purple-200"
                        on:click={() => {
                            feedLength = feedLength + 50;
                        }}
                    >
                        Show More...
                    </div>
                </div>
            {/if}
        {/if}
    </div>
</div>
