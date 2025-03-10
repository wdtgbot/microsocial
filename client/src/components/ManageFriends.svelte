<script>
    import { onMount, onDestroy } from "svelte";
    import * as timeago from "timeago.js";
    import anchorme from "anchorme";
    import { createAvatar } from "@dicebear/avatars";
    import * as style from "@dicebear/avatars-bottts-sprites";

    let hostAccessKey = "";
    let addFriendBridge;
    let friendListResp;
    let friendListLoaded = false;
    let myKeyLoaded = false;
    let hostUsername;
    let myNameLoaded;
    let anyPending = false;
    let viewingFriendProfile = false;
    let viewingProfile;
    let viewingName;
    let actualFriendCount = 0;
    let pendingFriendCount = 0;
    let viewingFriendsPosts = false;
    let viewingPosts;
    let howDoYouConnect = false;
    let hostBridge = window.location.hostname;

    let devBridge = "";

    if (hostBridge == "localhost") {
        devBridge = "https://41034m.deta.dev/";
    }

    onMount(async () => {
        getMyKey();
        getMyName();
    });

    onDestroy(async () => {
        clearInterval(checkFriends);
    });

    const getMyKey = async () => {
        var myKeyReq = await fetch(`${devBridge}my-key`);
        var myKeyResp = await myKeyReq.json();
        hostAccessKey = myKeyResp.key;
        myKeyLoaded = true;
        getFriends();
    };

    const getMyName = async () => {
        var myNameReq = await fetch(`${devBridge}public/profile`);
        var myNameResp = await myNameReq.json();
        hostUsername = myNameResp.username;
        myNameLoaded = true;
    };

    const removeFriend = async (key) => {
        var friendToDelete = {
            key: key,
            access_key: hostAccessKey,
        };

        var removeResp = await fetch(`${devBridge}remove-friend`, {
            method: "DELETE",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(friendToDelete),
        });

        var removeResult = await removeResp.json();
        getFriends();
        purgeCache();
    };

    const getFriends = async () => {
        var listReq = await fetch(
            devBridge +
                "friend-list?" +
                new URLSearchParams({
                    access_key: hostAccessKey,
                    pending: "true",
                })
        );
        friendListResp = await listReq.json();
        actualFriendCount = 0;
        friendListResp.forEach((friend) => {
            if (friend.category == "pending_friend") {
                pendingFriendCount++;
                anyPending = true;
            } else {
                if (friend.category == "friend") {
                    actualFriendCount++;
                }
            }
        });

        friendListLoaded = true;
    };

    const sendFriendRequest = async (bridge) => {
        // Lazy URL Trimming

        var friendReqContent = {
            access_key: hostAccessKey,
            name: hostUsername,
            bridge: hostBridge,
            public_key: hostAccessKey,
        };

        var friendReqURL = `https://${bridge
            .replace("https://", "")
            .replace("/", "")}/public/request`;
        var friendReqResp = await fetch(friendReqURL, {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(friendReqContent),
        });

        var friendResult = await friendReqResp.json();
        addFriendBridge = "";
        getFriends();
    };

    const acceptFriendRequest = async (bridge, key, name) => {
        var friendReqContent = {
            name: name,
            bridge: bridge,
            public_key: key,
        };

        var friendReqURL = `${devBridge}accept`;
        var friendReqResp = await fetch(friendReqURL, {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(friendReqContent),
        });

        var friendResult = await friendReqResp.json();
        sendFriendRequest(bridge);
        addFriendBridge = "";
        friendListLoaded = false;
        anyPending = false;
        getFriends();
        purgeCache();
    };

    const getFriendProfile = async (bridge) => {
        var friendURL = `https://${bridge}/public/profile`;
        var friendProfileReq = await fetch(friendURL);
        var friendProfileResp = await friendProfileReq.json();
        viewingProfile = friendProfileResp;
        viewingFriendProfile = true;
    };

    const getFriendPosts = async (bridge) => {
        if (hostBridge != "localhost") {
            var friendURL = `https://${hostBridge}/friend-posts?bridge=${bridge}`;
        } else {
            var friendURL = devBridge + "friend-posts?bridge=" + bridge;
        }

        var friendPostsReq = await fetch(friendURL);
        var friendPostsResp = await friendPostsReq.json();
        viewingPosts = friendPostsResp;
        viewingFriendsPosts = true;
    };

    function convertTimestamp(timestamp) {
        var dateObject = new Date(timestamp * 1000);
        var readableDate = dateObject.toLocaleString();
        return readableDate;
    }

    const purgeCache = async () => {
        var purgeCacheReq = await fetch(`${devBridge}purge/cache`);
        var purgeCacheResp = await purgeCacheReq.json();
    };

    const genAvatar = (value) => {
        var avatar = createAvatar(style, {
            seed: value,
        });
        return avatar;
    };

    // Intervals
    const checkFriends = setInterval(getFriends, 5000);
</script>

<div class="container w-full p-2 mx-auto sm:p-10 md:w-2/3 lg:w-1/2 xl:w-1/2">
    {#if viewingFriendProfile == false}
        <h2 class="pb-6 text-2xl text-center">
            <svg
                class="inline-block mb-2 w-7 h-7"
                fill="currentColor"
                viewBox="0 0 20 20"
                xmlns="http://www.w3.org/2000/svg"
                ><path
                    d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"
                /></svg
            >
            Manage Friends
        </h2>
        <div
            class="flex w-full p-2 m-auto bg-gray-200 border border-gray-300 rounded-lg shadow-lg md:w-3/4 dark:bg-truegray-800 dark:border-truegray-900"
        >
            <div
                class="w-full p-2 border border-gray-300 rounded dark:border-truegray-600"
            >
                <div
                    class="flex items-center p-2 bg-gray-300 border rounded dark:bg-truegray-900 dark:border-truegray-800"
                >
                    <svg
                        class="mr-2 dark:text-truegray-200"
                        width="24"
                        height="24"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                        ><path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                        /></svg
                    >
                    <input
                        bind:value={addFriendBridge}
                        type="text"
                        placeholder="Microsocial Server URL"
                        class="w-full text-gray-700 bg-gray-300 focus:outline-none dark:bg-truegray-900 dark:text-truegray-300"
                    />
                </div>
            </div>
            {#if addFriendBridge}
                <button
                    title="Add Friend"
                    on:click={async () => {
                        sendFriendRequest(addFriendBridge);
                        alert("Friend Request Sent! (If Valid)");
                    }}
                    class="p-2 m-2 ml-4 text-white bg-green-500 border hover:bg-green-400 rounded-3xl focus:outline-none dark:bg-truegray-700 dark:hover:bg-truegray-600 dark:border-truegray-600"
                    ><svg
                        class="w-6 h-6 dark:text-truegray-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                        xmlns="http://www.w3.org/2000/svg"
                        ><path
                            d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z"
                        /></svg
                    ></button
                >
            {:else}
                <button
                    title="Add Friend"
                    on:click={async () => {
                        alert(
                            "You need to enter a valid Microsocial server URL"
                        );
                    }}
                    class="p-2 m-2 ml-4 text-white border border-truegray-300 bg-truegray-300 dark:bg-truegray-900 dark:border-truegray-700 rounded-3xl focus:outline-none"
                    ><svg
                        class="w-6 h-6 dark:text-truegray-600"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                        xmlns="http://www.w3.org/2000/svg"
                        ><path
                            d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z"
                        /></svg
                    ></button
                >
            {/if}
        </div>
        <div class="flex ">
            <div class="m-auto">
                <button
                    on:click={() => {
                        howDoYouConnect = !howDoYouConnect;
                    }}
                    class="text-xs underline text-sky-700 focus:outline-none"
                    >How does this work?</button
                >
            </div>
        </div>
        {#if howDoYouConnect == true || (actualFriendCount == 0 && pendingFriendCount == 0 && friendListLoaded == true)}
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
                    <p class="p-2 text-sm md:p-0">
                        To connect with friends simply enter the URL that points
                        to their Microsocial deployment in the form above, if
                        they accept your request you'll get one back so don't
                        forget to come back and accept it! Your Microsocial
                        server URL is <span
                            class="text-blue-800 dark:text-amber-400"
                            >{hostBridge}</span
                        > share it with your friends so they can connect with you.
                        Friends and any pending requests will be displayed below
                        where you can manage them and do things like view their profiles.
                    </p>
                </div>
            </div>
        {/if}

        {#if friendListLoaded}
            {#if actualFriendCount > 0}
                <h2 class="pt-4 pb-2 text-2xl">Friends</h2>

                {#each friendListResp as { bridge, name, key, category }}
                    {#if category != "pending_friend"}
                        <div
                            class="flex w-full mb-2 text-gray-600 bg-gray-200 rounded shadow dark:bg-truegray-800 dark:text-gray-300"
                        >
                            <div
                                class="self-center w-12 h-12 pt-2 mt-2 ml-2 md:my-1 md:mb-3"
                            >
                                {@html genAvatar(name)}
                            </div>
                            <div class="self-center w-full p-2">
                                <div>{name}</div>
                                <div class="-mt-1 text-xs text-gray-400 title">
                                    {bridge}
                                </div>
                            </div>

                            <div class="self-center p-2 sec w-2/8">
                                <div class="flex text-xs font-light">
                                    <button
                                        title="Remove Friend"
                                        class="p-2 mr-1 rounded shadow cursor-pointer hover:bg-red-100 dark:hover:bg-red-500 focus:outline-none"
                                        on:click={() => {
                                            if (
                                                confirm(
                                                    `Are you sure you want to remove ${name} as a friend?`
                                                )
                                            ) {
                                                removeFriend(key);
                                            }
                                        }}
                                    >
                                        <svg
                                            class="w-6 h-6"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                            xmlns="http://www.w3.org/2000/svg"
                                            ><path
                                                fill-rule="evenodd"
                                                d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                                                clip-rule="evenodd"
                                            /></svg
                                        >
                                    </button>
                                    <button
                                        title="View Profile"
                                        class="p-2 mr-1 rounded shadow cursor-pointer hover:bg-indigo-100 dark:hover:bg-indigo-500 focus:outline-none"
                                        on:click={() => {
                                            viewingName = name;
                                            getFriendProfile(bridge);
                                            getFriendPosts(bridge);
                                        }}
                                    >
                                        <svg
                                            class="w-6 h-6"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                            xmlns="http://www.w3.org/2000/svg"
                                            ><path
                                                d="M10 12a2 2 0 100-4 2 2 0 000 4z"
                                            /><path
                                                fill-rule="evenodd"
                                                d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                                                clip-rule="evenodd"
                                            /></svg
                                        >
                                    </button>
                                </div>
                            </div>
                        </div>
                    {/if}
                {/each}
            {/if}

            {#if anyPending == true}
                {#if pendingFriendCount > 0}
                    <h2 class="pt-4 pb-2 text-2xl">Requests</h2>
                {/if}
                {#each friendListResp as { bridge, name, key, category }}
                    {#if category == "pending_friend"}
                        <div
                            class="flex w-full mb-2 text-gray-600 bg-gray-200 rounded shadow dark:bg-truegray-800 dark:text-gray-300"
                        >
                            <div class="self-center w-full p-2">
                                <div class="flex">
                                    <div>{name}</div>
                                </div>

                                <div class="-mt-1 text-xs text-gray-400 title">
                                    {bridge}
                                </div>
                            </div>
                            <div class="self-center p-2 sec w-2/8">
                                <div class="flex text-xs font-light">
                                    <button
                                        title="Accept Friend Request"
                                        class="p-2 mr-1 rounded shadow cursor-pointer hover:bg-green-100 focus:outline-none dark:hover:bg-green-500"
                                        on:click={() => {
                                            acceptFriendRequest(
                                                bridge,
                                                key,
                                                name
                                            );
                                            --pendingFriendCount;
                                        }}
                                        ><svg
                                            class="w-6 h-6"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                            xmlns="http://www.w3.org/2000/svg"
                                            ><path
                                                fill-rule="evenodd"
                                                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                                clip-rule="evenodd"
                                            /></svg
                                        >
                                    </button>
                                    <button
                                        title="Decline Friend Request"
                                        class="p-2 mr-1 rounded shadow cursor-pointer hover:bg-red-100 focus:outline-none dark:hover:bg-red-500"
                                        on:click={() => {
                                            removeFriend(key);
                                            --pendingFriendCount;
                                        }}
                                        ><svg
                                            class="w-6 h-6"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                            xmlns="http://www.w3.org/2000/svg"
                                            ><path
                                                fill-rule="evenodd"
                                                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                                clip-rule="evenodd"
                                            /></svg
                                        >
                                    </button>
                                </div>
                            </div>
                        </div>
                    {/if}
                {/each}
            {/if}
        {/if}
    {:else}
        <div class="p-1">
            <div
                class="p-4 bg-gray-200 border-2 rounded-lg shadow-lg dark:bg-truegray-800 dark:border-truegray-900"
            >
                <div class="flex">
                    <div class="w-8 md:w-12">
                        {@html genAvatar(viewingProfile.username)}
                    </div>
                    <h2
                        class="mt-2 mb-2 ml-2 text-sm md:mt-3 lg:text-2xl md:text-xl"
                    >
                        {viewingProfile.username}
                    </h2>
                    <button
                        class="ml-auto "
                        title="Close Profile"
                        on:click={() => {
                            viewingFriendProfile = false;
                        }}
                    >
                        <svg
                            class="w-8 h-8 text-pink-700"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                            xmlns="http://www.w3.org/2000/svg"
                            ><path
                                fill-rule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                clip-rule="evenodd"
                            /></svg
                        >
                    </button>
                </div>

                <p
                    class="py-4 mt-2 text-sm text-gray-600 border-t border-b border-gray-300 md:text-sm dark:text-truegray-300 dark:border-gray-700"
                >
                    {viewingProfile.bio}
                </p>
                {#if viewingFriendsPosts}
                    <p class="mt-2">
                        <svg
                            class="inline w-6 h-6 mr-2"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                            xmlns="http://www.w3.org/2000/svg"
                            ><path
                                fill-rule="evenodd"
                                d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z"
                                clip-rule="evenodd"
                            /></svg
                        >{viewingPosts.length}
                    </p>
                {/if}
            </div>
        </div>
        {#if viewingFriendsPosts}
            {#each viewingPosts as { value, time }}
                <div class="p-1">
                    <div
                        class="p-4 bg-gray-200 border-2 rounded-lg shadow-lg dark:bg-truegray-800 dark:border-truegray-900"
                    >
                        <div class="flex">
                            <div
                                class="flex items-center text-xs text-gray-400"
                            >
                                <p>{convertTimestamp(time)}</p>
                                <p class="px-1">•</p>
                                <p>
                                    {timeago.format(convertTimestamp(time))}
                                </p>
                            </div>
                        </div>
                        <div class="mt-2">
                            <p
                                class="text-sm text-gray-600 dark:text-truegray-300"
                            >
                                {@html anchorme(value)}
                            </p>
                        </div>
                    </div>
                </div>
            {/each}
        {/if}
    {/if}
</div>
