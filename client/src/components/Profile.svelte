<script>
    import { onMount, onDestroy } from "svelte";
    import * as timeago from "timeago.js";
    import anchorme from "anchorme";
    import { createAvatar } from "@dicebear/avatars";
    import * as style from "@dicebear/avatars-bottts-sprites";

    let hostAccessKey = "";
    let myKeyLoaded = false;
    let hostUsername = "";
    let hostProfileLoaded = false;
    let hostBridge = window.location.hostname;
    let hostBio = "";
    let hostPostsLoaded = false;
    let hostPosts;
    let postsLength = 50;

    let devBridge = "";

    if (hostBridge == "localhost") {
        devBridge = "https://41034m.deta.dev/";
    }

    onMount(async () => {
        getMyKey();
        getMyProfile();
    });

    onDestroy(async () => {});

    const getMyKey = async () => {
        var myKeyReq = await fetch(`${devBridge}my-key`);
        var myKeyResp = await myKeyReq.json();
        hostAccessKey = myKeyResp.key;
        myKeyLoaded = true;
        getHostPosts();
    };

    const getMyProfile = async () => {
        var hostProfileReq = await fetch(`${devBridge}public/profile`);
        var hostProfileResp = await hostProfileReq.json();
        hostUsername = hostProfileResp.username;
        hostBio = hostProfileResp.bio;
        hostProfileLoaded = true;
    };

    const getHostPosts = async () => {
        var postsURL = `${devBridge}public/shared-posts?key=${hostAccessKey}`;
        var hostPostsReq = await fetch(postsURL);
        var hostPostsResp = await hostPostsReq.json();
        hostPosts = hostPostsResp;

        // Add Index
        hostPosts = hostPosts.map((item, index) => ({
            index,
            ...item,
        }));

        hostPostsLoaded = true;
    };

    function convertTimestamp(timestamp) {
        var dateObject = new Date(timestamp * 1000);
        var readableDate = dateObject.toLocaleString();
        return readableDate;
    }

    const genAvatar = (value) => {
        var avatar = createAvatar(style, {
            seed: value,
        });
        return avatar;
    };
</script>

<div class="container w-full p-2 mx-auto sm:p-10 md:w-2/3 lg:w-1/2 xl:w-1/2">
    {#if hostProfileLoaded}
        <div class="p-1">
            <div
                class="p-4 bg-gray-200 border-2 rounded-lg shadow-lg dark:bg-truegray-800 dark:border-truegray-900"
            >
                <div class="flex">
                    <div class="w-8 md:w-12">
                        {@html genAvatar(hostUsername)}
                    </div>
                    <h2
                        class="mt-2 mb-2 ml-2 text-sm md:mt-3 lg:text-2xl md:text-xl"
                    >
                        {hostUsername}
                    </h2>
                </div>

                <p
                    class="py-4 mt-2 text-sm text-gray-600 border-t border-b border-gray-300 md:text-sm dark:text-truegray-300 dark:border-gray-700"
                >
                    {hostBio}
                </p>
                {#if hostPostsLoaded}
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
                        >{hostPosts.length}
                    </p>
                {/if}
            </div>
        </div>
    {/if}
    {#if hostPostsLoaded}
        {#if hostPostsLoaded && hostPosts.length < 1}
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
                        Head over to the live feed tab and you can create some
                        posts for your friends to see.
                    </p>
                </div>
            </div>
        {/if}
        {#each hostPosts as { value, time, reactions, index }}
            {#if index < postsLength}
                <div class="p-1">
                    <div
                        class="p-4 bg-gray-200 border-2 border-gray-300 rounded-lg shadow-lg dark:bg-truegray-800 dark:border-truegray-900"
                    >
                        <div class="flex">
                            <div
                                class="flex items-center text-sm text-gray-400"
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
                        {#if reactions.length != 0 && hostProfileLoaded}
                            <div
                                class="flex flex-shrink pl-2 pr-2 mt-2 -mb-3 bg-purple-900 border border-purple-800 cursor-default rounded-2xl w-min"
                            >
                                {#each reactions as { emoji, reacting }}
                                    <span title={reacting} class="ml-1 mr-1"
                                        >{emoji}</span
                                    >
                                {/each}
                            </div>
                        {/if}
                    </div>
                </div>
            {/if}
        {/each}
        {#if postsLength < hostPosts.length}
            <div class="flex items-center justify-center py-4">
                <div
                    class="px-3 py-2 text-purple-200 bg-purple-600 border-2 border-purple-500 rounded-lg cursor-pointer hover:bg-purple-700 hover:border-purple-600 hover:text-purple-200"
                    on:click={() => {
                        postsLength = postsLength + 50;
                    }}
                >
                    Show More...
                </div>
            </div>
        {/if}
    {/if}
</div>
