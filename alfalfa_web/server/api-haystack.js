/**
 * @openapi
 * /about:
 *   get:
 *     description: Summary information for server
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: about response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /formats:
 *   get:
 *     description: Grid data formats supported by this server
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: formats response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /hisRead:
 *   get:
 *     description: Read time series from historian
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: hisRead response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /invokeAction:
 *   get:
 *     description: Invoke action on target entity
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: invokeAction response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /nav:
 *   get:
 *     description: Navigate record tree
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: nav response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /ops:
 *   get:
 *     description: Operations supported by this server
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: ops response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /pointWrite:
 *   get:
 *     description: Read/write writable point priority array
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: pointWrite response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /read:
 *   get:
 *     description: Read entity records in database
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: read response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchPoll:
 *   get:
 *     description: Watch poll cov or refresh
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: watchPoll response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchSub:
 *   get:
 *     description: Watch subscription
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: watchSub response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchUnsub:
 *   get:
 *     description: Watch unsubscription
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: watchUnsub response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */
