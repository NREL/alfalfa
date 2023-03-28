/**
 * @openapi
 * /about:
 *   get:
 *     operationId: About
 *     description: |
 *       Summary information for server
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#about" target="_blank">About op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: About response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /formats:
 *   get:
 *     operationId: Formats
 *     description: |
 *       Grid data formats supported by this server
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Filetypes" target="_blank">Filetypes documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: Formats response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /hisRead:
 *   get:
 *     operationId: HisRead
 *     description: |
 *       Read time series from historian
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#hisRead" target="_blank">HisRead op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: HisRead response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /nav:
 *   get:
 *     operationId: Nav
 *     description: |
 *       Navigate record tree
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#nav" target="_blank">Nav op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: Nav response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /ops:
 *   get:
 *     operationId: Ops
 *     description: |
 *       Operations supported by this server
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#ops" target="_blank">Ops op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: Ops response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /pointWrite:
 *   get:
 *     operationId: PointWrite
 *     description: |
 *       Read/write writable point priority array
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#pointWrite" target="_blank">PointWrite op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: PointWrite response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /read:
 *   get:
 *     operationId: Read
 *     description: |
 *       Read entity records in database
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#read" target="_blank">Read op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: Read response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchPoll:
 *   get:
 *     operationId: WatchPoll
 *     description: |
 *       Watch poll COV or refresh
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#watchPoll" target="_blank">WatchPoll op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: WatchPoll response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchSub:
 *   get:
 *     operationId: WatchSub
 *     description: |
 *       Watch subscription
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#watchSub" target="_blank">WatchSub op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: WatchSub response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchUnsub:
 *   get:
 *     operationId: WatchUnsub
 *     description: |
 *       Watch unsubscription
 *
 *       <a href="https://project-haystack.org/doc/docHaystack/Ops#watchUnsub" target="_blank">WatchUnsub op documentation</a>
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: WatchUnsub response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */
