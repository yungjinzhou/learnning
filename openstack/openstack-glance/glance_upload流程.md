## openstack镜像上传源码分析



上传接口  /v2/images/imge_id/file  方法 PUT

从api代码入手

1. 从glance/api/v2/router.py中路由对应关系

```
 # from glance.api.v2 import image_data       
        
        
        image_data_resource = image_data.create_resource()
        mapper.connect('/images/{image_id}/file',
                       controller=image_data_resource,
                       action='download',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/images/{image_id}/file',
                       controller=image_data_resource,
                       action='upload',
                       conditions={'method': ['PUT']})
        mapper.connect('/images/{image_id}/file',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='GET, PUT')
```

可以看出调用了image_data的upload方法

```
class ImageDataController(object):
  .............

    @utils.mutating
    def upload(self, req, image_id, data, size):
        import time
        begin_api_time = time.time()
        backend = None
        if CONF.enabled_backends:
            backend = req.headers.get('x-image-meta-store',
                                      CONF.glance_store.default_backend)

            try:
                glance_store.get_store_from_store_identifier(backend)
            except glance_store.UnknownScheme as exc:
                raise webob.exc.HTTPBadRequest(explanation=exc.msg,
                                               request=req,
                                               content_type='text/plain')

        image_repo = self.gateway.get_repo(req.context)
        image = None
        refresher = None
        cxt = req.context
        try:
            self.policy.enforce(cxt, 'upload_image', {})
            image = image_repo.get(image_id)
            image.status = 'saving'
            try:
                if CONF.data_api == 'glance.db.registry.api':
                    # create a trust if backend is registry
                    try:
                        # request user plugin for current token
                        user_plugin = req.environ.get('keystone.token_auth')
                        roles = []
                        # use roles from request environment because they
                        # are not transformed to lower-case unlike cxt.roles
                        for role_info in req.environ.get(
                                'keystone.token_info')['token']['roles']:
                            roles.append(role_info['name'])
                        refresher = trust_auth.TokenRefresher(user_plugin,
                                                              cxt.project_id,
                                                              roles)
                    except Exception as e:
                        LOG.info(_LI("Unable to create trust: %s "
                                     "Use the existing user token."),
                                 encodeutils.exception_to_unicode(e))

                # image_repo---, <glance.api.authorization.ImageRepoProxy object at 0x7f8f989fa110>
                image_repo.save(image, from_state='queued')
                # image---, <glance.api.authorization.ImageProxy object at 0x7f8f9893a690>
                image.set_data(data, size, backend=backend)
                try:
                    # image_repo: glance.api.authorization.ImageRepoProxy object at 0x7fc79a073910>
                    image_repo.save(image, from_state='saving')
                except exception.NotAuthenticated:
                    if refresher is not None:
                        # request a new token to update an image in database
                        cxt.auth_token = refresher.refresh_token()
                        image_repo = self.gateway.get_repo(req.context)
                        image_repo.save(image, from_state='saving')
                    else:
                        raise

                try:
                    # release resources required for re-auth
                    if refresher is not None:
                        refresher.release_resources()
                except Exception as e:
                    LOG.info(_LI("Unable to delete trust %(trust)s: %(msg)s"),
                             {"trust": refresher.trust_id,
                              "msg": encodeutils.exception_to_unicode(e)})

            except (glance_store.NotFound,
                    exception.ImageNotFound,
                    exception.Conflict):
                msg = (_("Image %s could not be found after upload. "
                         "The image may have been deleted during the "
                         "upload, cleaning up the chunks uploaded.") %
                       image_id)
                LOG.warn(msg)
                # NOTE(sridevi): Cleaning up the uploaded chunks.
                try:
                    image.delete()
                except exception.ImageNotFound:
                    # NOTE(sridevi): Ignore this exception
                    pass
                raise webob.exc.HTTPGone(explanation=msg,
                                         request=req,
                                         content_type='text/plain')
            except exception.NotAuthenticated:
                msg = (_("Authentication error - the token may have "
                         "expired during file upload. Deleting image data for "
                         "%s.") % image_id)
                LOG.debug(msg)
                try:
                    image.delete()
                except exception.NotAuthenticated:
                    # NOTE: Ignore this exception
                    pass
                raise webob.exc.HTTPUnauthorized(explanation=msg,
                                                 request=req,
                                                 content_type='text/plain')
        except ValueError as e:
            LOG.debug("Cannot save data for image %(id)s: %(e)s",
                      {'id': image_id,
                       'e': encodeutils.exception_to_unicode(e)})
            self._restore(image_repo, image)
            raise webob.exc.HTTPBadRequest(
                explanation=encodeutils.exception_to_unicode(e))

        except glance_store.StoreAddDisabled:
            msg = _("Error in store configuration. Adding images to store "
                    "is disabled.")
            LOG.exception(msg)
            self._restore(image_repo, image)
            raise webob.exc.HTTPGone(explanation=msg, request=req,
                                     content_type='text/plain')

        except exception.InvalidImageStatusTransition as e:
            msg = encodeutils.exception_to_unicode(e)
            LOG.exception(msg)
            raise webob.exc.HTTPConflict(explanation=e.msg, request=req)

        except exception.Forbidden as e:
            msg = ("Not allowed to upload image data for image %s" %
                   image_id)
            LOG.debug(msg)
            raise webob.exc.HTTPForbidden(explanation=msg, request=req)

        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.msg)

        except glance_store.StorageFull as e:
            msg = _("Image storage media "
                    "is full: %s") % encodeutils.exception_to_unicode(e)
            LOG.error(msg)
            self._restore(image_repo, image)
            raise webob.exc.HTTPRequestEntityTooLarge(explanation=msg,
                                                      request=req)

        except exception.StorageQuotaFull as e:
            msg = _("Image exceeds the storage "
                    "quota: %s") % encodeutils.exception_to_unicode(e)
            LOG.error(msg)
            self._restore(image_repo, image)
            raise webob.exc.HTTPRequestEntityTooLarge(explanation=msg,
                                                      request=req)

        except exception.ImageSizeLimitExceeded as e:
            msg = _("The incoming image is "
                    "too large: %s") % encodeutils.exception_to_unicode(e)
            LOG.error(msg)
            self._restore(image_repo, image)
            raise webob.exc.HTTPRequestEntityTooLarge(explanation=msg,
                                                      request=req)

        except glance_store.StorageWriteDenied as e:
            msg = _("Insufficient permissions on image "
                    "storage media: %s") % encodeutils.exception_to_unicode(e)
            LOG.error(msg)
            self._restore(image_repo, image)
            raise webob.exc.HTTPServiceUnavailable(explanation=msg,
                                                   request=req)

        except cursive_exception.SignatureVerificationError as e:
            msg = (_LE("Signature verification failed for image %(id)s: %(e)s")
                   % {'id': image_id,
                      'e': encodeutils.exception_to_unicode(e)})
            LOG.error(msg)
            self._delete(image_repo, image)
            raise webob.exc.HTTPBadRequest(explanation=msg)

        except webob.exc.HTTPGone as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to upload image data due to HTTP error"))

        except webob.exc.HTTPError as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to upload image data due to HTTP error"))
                self._restore(image_repo, image)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to upload image data due to "
                              "internal error"))
                self._restore(image_repo, image)

```

image.set_data调用了lance.api.authorization.ImageProxy里的set_data

而ImageProxy继承glance.domain.proxy.Image

```
class ImageProxy(glance.domain.proxy.Image):

    def __init__(self, image, context):
        self.image = image
        self.context = context
        super(ImageProxy, self).__init__(image)

```

找到Image里的set_data

```
class Image(object):

	.............
    def set_data(self, data, size=None, backend=None):
        # -sefl.base', <glance.notifier.ImageProxy object at 0x7fa6a15a6c90>)
        self.base.set_data(data, size, backend=backend)
```

根据self.base定位glance.notifier.ImageProxy中的方法

```
    def set_data(self, data, size=None, backend=None):
        self.send_notification('image.prepare', self.repo, backend=backend)

        notify_error = self.notifier.error
        try:
        	# (<glance.api.policy.ImageProxy object at 0x7f51ab96c890>, 'self.repo
            self.repo.set_data(data, size, backend=backend)
        except glance_store.StorageFull as e:
            msg = (_("Image storage media is full: %s") %
                   encodeutils.exception_to_unicode(e))
            _send_notification(notify_error, 'image.upload', msg)
            raise webob.exc.HTTPRequestEntityTooLarge(explanation=msg)
        ................
        else:
            self.send_notification('image.upload', self.repo)
            self.send_notification('image.activate', self.repo)
```

定位self.repo: glance.api.policy.ImageProxy， 找到ImageProxy的set_data

```

    def set_data(self, *args, **kwargs):
        return self.image.set_data(*args, **kwargs)
```



self.image:   glance.quota.ImageProxy

```

    def set_data(self, data, size=None, backend=None):
       .........
        self.image.set_data(data, size=size, backend=backend)
		.......
        try:
            glance.api.common.check_quota(
                self.context, self.image.size, self.db_api,
                image_id=self.image.image_id)
        except exception.StorageQuotaFull:
            with excutils.save_and_reraise_exception():
                LOG.info(_LI('Cleaning up %s after exceeding the quota.'),
                         self.image.image_id)
                self.store_utils.safe_delete_from_backend(
                    self.context, self.image.image_id, self.image.locations[0])
```

转到glance.location.ImageProxy的set_data

self.iamge---quota------', <glance.location.ImageProxy

根据定位流程，走到如下分支

```javascript
    def set_data(self, data, size=None, backend=None):
        。。。。。。。。
        if CONF.enabled_backends:
            (location, size, checksum,
             multihash, loc_meta) = self.store_api.add_with_multihash(
                CONF,
                self.image.image_id,
                utils.LimitingReader(utils.CooperativeReader(data),
                                     CONF.image_size_cap),
                size,
                backend,
                hashing_algo,
                context=self.context,
                verifier=verifier)
        else:
            # 走下面流程
            (location,
             size,
             checksum,
             multihash,
             loc_meta) = self.store_api.add_to_backend_with_multihash(
                CONF,
                self.image.image_id,
                utils.LimitingReader(utils.CooperativeReader(data),
                                     CONF.image_size_cap),
                size,
                hashing_algo,
                context=self.context,
                verifier=verifier)

        # NOTE(bpoulos): if verification fails, exception will be raised
       ..............

```

根据定位流程，走到如下分支

```
self.store_api.add_to_backend_with_multihash(
   。。。。。


2022-04-11 10:11:32.017 59975 ERROR glance.common.wsgi   File "/usr/lib/python2.7/site-packages/glance_store/driver.py", line 274, in add_adapter

```



```
# /usr/lib/python2.7/site-packages/glance_store/backend.py", line 541, in add_to_backend_with_multihash


def add_to_backend_with_multihash(conf, image_id, data, size, hashing_algo,
                                  scheme=None, context=None, verifier=None):
    if scheme is None:
        scheme = conf['glance_store']['default_store']
    store = get_store_from_scheme(scheme)
    return store_add_to_backend_with_multihash(
        image_id, data, size, hashing_algo, store, context, verifier)

```

根据store对象，找到对应的drvier里的add方法

如果配置的rbd

```
# /usr/lib/python2.7/site-packages/glance_store/_drivers/rbd.py



    @driver.back_compat_add
    @capabilities.check
    def add(self, image_id, image_file, image_size, hashing_algo, context=None,
            verifier=None):
        """
        Stores an image file with supplied identifier to the backend
        storage system and returns a tuple containing information
        about the stored image.

        :param image_id: The opaque image identifier
        :param image_file: The image data to write, as a file-like object
        :param image_size: The size of the image data to write, in bytes
        :param hashing_algo: A hashlib algorithm identifier (string)
        :param context: A context object
        :param verifier: An object used to verify signatures for images

        :returns: tuple of: (1) URL in backing store, (2) bytes written,
                  (3) checksum, (4) multihash value, and (5) a dictionary
                  with storage system specific information
        :raises: `glance_store.exceptions.Duplicate` if the image already
                 exists
        """
        checksum = hashlib.md5()
        os_hash_value = hashlib.new(str(hashing_algo))
        image_name = str(image_id)
        with self.get_connection(conffile=self.conf_file,
                                 rados_id=self.user) as conn:
            fsid = None
            if hasattr(conn, 'get_fsid'):
                # Librados's get_fsid is represented as binary
                # in py3 instead of str as it is in py2.
                # This is causing problems with ceph.
                # Decode binary to str fixes these issues.
                # Fix with encodeutils.safe_decode CAN BE REMOVED
                # after librados's fix will be stable.
                #
                # More informations:
                # https://bugs.launchpad.net/glance-store/+bug/1816721
                # https://bugs.launchpad.net/cinder/+bug/1816468
                # https://tracker.ceph.com/issues/38381
                fsid = encodeutils.safe_decode(conn.get_fsid())
            with conn.open_ioctx(self.pool) as ioctx:
                order = int(math.log(self.WRITE_CHUNKSIZE, 2))
                LOG.debug('creating image %s with order %d and size %d',
                          image_name, order, image_size)
                if image_size == 0:
                    LOG.warning(_("since image size is zero we will be doing "
                                  "resize-before-write for each chunk which "
                                  "will be considerably slower than normal"))

                try:
                    loc = self._create_image(fsid, conn, ioctx, image_name,
                                             image_size, order)
                except rbd.ImageExists:
                    msg = _('RBD image %s already exists') % image_id
                    raise exceptions.Duplicate(message=msg)

                try:
                    with rbd.Image(ioctx, image_name) as image:
                        bytes_written = 0
                        offset = 0
                        chunks = utils.chunkreadable(image_file,
                                                     self.WRITE_CHUNKSIZE)
                        for chunk in chunks:
                            # If the image size provided is zero we need to do
                            # a resize for the amount we are writing. This will
                            # be slower so setting a higher chunk size may
                            # speed things up a bit.
                            if image_size == 0:
                                chunk_length = len(chunk)
                                length = offset + chunk_length
                                bytes_written += chunk_length
                                LOG.debug(_("resizing image to %s KiB") %
                                          (length / units.Ki))
                                image.resize(length)
                            LOG.debug(_("writing chunk at offset %s") %
                                      (offset))
                            offset += image.write(chunk, offset)
                            os_hash_value.update(chunk)
                            checksum.update(chunk)
                            if verifier:
                                verifier.update(chunk)
                        if loc.snapshot:
                            image.create_snap(loc.snapshot)
                            image.protect_snap(loc.snapshot)
                except rbd.NoSpace:
                    log_msg = (_LE("Failed to store image %(img_name)s "
                                   "insufficient space available") %
                               {'img_name': image_name})
                    LOG.error(log_msg)

                    # Delete image if one was created
                    try:
                        target_pool = loc.pool or self.pool
                        self._delete_image(target_pool, loc.image,
                                           loc.snapshot)
                    except exceptions.NotFound:
                        pass

                    raise exceptions.StorageFull(message=log_msg)
                except Exception as exc:
                    log_msg = (_LE("Failed to store image %(img_name)s "
                                   "Store Exception %(store_exc)s") %
                               {'img_name': image_name,
                                'store_exc': exc})
                    LOG.error(log_msg)

                    # Delete image if one was created
                    try:
                        target_pool = loc.pool or self.pool
                        self._delete_image(target_pool, loc.image,
                                           loc.snapshot)
                    except exceptions.NotFound:
                        pass

                    raise exc

        # Make sure we send back the image size whether provided or inferred.
        if image_size == 0:
            image_size = bytes_written

        # Add store backend information to location metadata
        metadata = {}
        if self.backend_group:
            metadata['backend'] = u"%s" % self.backend_group

        return (loc.get_uri(),
                image_size,
                checksum.hexdigest(),
                os_hash_value.hexdigest(),
                metadata)



```





## 增加glance上传时的进度条数据

修改/usr/lib/python2.7/site_packages/glance_store/_drivers/rbd.py

```
    @driver.back_compat_add
    @capabilities.check
    def add(self, image_id, image_file, image_size, hashing_algo, context=None,
            verifier=None):
        """
       ..........
       # 增加代码
        import memcache
        remote_cache = memcache.Client(["controller:11211"], debug=True)
        with open("/etc/glance/glance-api.conf", "r") as f:
            line_contents = f.readlines()
            for line_content in line_contents:
                if "memcached_servers =" in line_content and "NONE" not in line_content:
                    memcache_address = line_content.strip().split("=")[1].strip()
                    if memcache_address not in ["controller:11211"]:
                        remote_cache = memcache.Client([memcache_address], debug=True)
                    break
        if image_size:
            remote_cache.set("{}_total_size".format(image_id), image_size, 86400)
        else:
            remote_cache.set("{}_total_size".format(image_id), 1, 86400)
            remote_cache.set("{}_uploading_size", 0, 86400)
        。。。。。。。。。
        with self.get_connection(conffile=self.conf_file,
                                 rados_id=self.user) as conn:
            。。。。。。。
            with conn.open_ioctx(self.pool) as ioctx:
                。。。。。。

                try:
                    with rbd.Image(ioctx, image_name) as image:
                        bytes_written = 0
                        offset = 0
                        chunks = utils.chunkreadable(image_file,
                                                     self.WRITE_CHUNKSIZE)
                        for chunk in chunks:
                            。。。。。。。。。。
                            offset += image.write(chunk, offset)
                            # 增加代码
                            if image_size:
                                remote_cache.set("{}_uploading_size".format(image_id), offset, 86400)
                            os_hash_value.update(chunk)
                            checksum.update(chunk)
                            if verifier:
                                verifier.update(chunk)
                        if loc.snapshot:
                            image.create_snap(loc.snapshot)
                            image.protect_snap(loc.snapshot)
                。。。。。。。。。。

        # Make sure we send back the image size whether provided or inferred.
        if image_size == 0:
            image_size = bytes_written
        # 增加代码
        remote_cache.set("{}_uploading_size", image_size, 86400)
```





修改/usr/lib/python2.7/site_packages/glance_store/_drivers/cinder.py

```
    @glance_store.driver.back_compat_add
    @capabilities.check
    def add(self, image_id, image_file, image_size, hashing_algo, context=None,
            verifier=None):
        """
        Stores an image file with supplied identifier to the backend
        storage system and returns a tuple containing information
        about the stored image.

        :param image_id: The opaque image identifier
        :param image_file: The image data to write, as a file-like object
        :param image_size: The size of the image data to write, in bytes
        :param hashing_algo: A hashlib algorithm identifier (string)
        :param context: The request context
        :param verifier: An object used to verify signatures for images

        :returns: tuple of: (1) URL in backing store, (2) bytes written,
                  (3) checksum, (4) multihash value, and (5) a dictionary
                  with storage system specific information
        :raises: `glance_store.exceptions.Duplicate` if the image already
                 exists
        """

        self._check_context(context, require_tenant=True)
        client = get_cinderclient(self.conf, context,
                                  backend=self.backend_group)
        os_hash_value = hashlib.new(str(hashing_algo))
        checksum = hashlib.md5()
        import memcache
        remote_cache = memcache.Client(["controller:11211"], debug=True)
        with open("/etc/glance/glance-api.conf", "r") as f:
            line_contents = f.readlines()
            for line_content in line_contents:
                if "memcached_servers =" in line_content and "NONE" not in line_content:
                    memcache_address = line_content.strip().split("=")[1].strip()
                    if memcache_address not in ["controller:11211"]:
                        remote_cache = memcache.Client([memcache_address], debug=True)
                    break
        if image_size:
            remote_cache.set("{}_total_size".format(image_id), image_size, 86400)
        else:
            remote_cache.set("{}_total_size".format(image_id), 1, 86400)
            remote_cache.set("{}_uploading_size", 0, 86400)
        bytes_written = 0

        size_gb = int(math.ceil(float(image_size) / units.Gi))
        if size_gb == 0:
            size_gb = 1
        name = "image-%s" % image_id
        owner = context.tenant
        metadata = {'glance_image_id': image_id,
                    'image_size': str(image_size),
                    'image_owner': owner}

        if self.backend_group:
            volume_type = getattr(self.conf,
                                  self.backend_group).cinder_volume_type
        else:
            volume_type = self.conf.glance_store.cinder_volume_type

        LOG.debug('Creating a new volume: image_size=%d size_gb=%d type=%s',
                  image_size, size_gb, volume_type or 'None')
        if image_size == 0:
            LOG.info(_LI("Since image size is zero, we will be doing "
                         "resize-before-write for each GB which "
                         "will be considerably slower than normal."))
        volume = client.volumes.create(size_gb, name=name, metadata=metadata,
                                       volume_type=volume_type)
        volume = self._wait_volume_status(volume, 'creating', 'available')
        size_gb = volume.size

        failed = True
        need_extend = True
        buf = None
        try:
            while need_extend:
                with self._open_cinder_volume(client, volume, 'wb') as f:
                    f.seek(bytes_written)
                    if buf:
                        f.write(buf)
                        bytes_written += len(buf)
                    while True:
                        buf = image_file.read(self.WRITE_CHUNKSIZE)
                        if not buf:
                            need_extend = False
                            break
                        os_hash_value.update(buf)
                        checksum.update(buf)
                        if verifier:
                            verifier.update(buf)
                        if (bytes_written + len(buf) > size_gb * units.Gi and
                                image_size == 0):
                            break
                        f.write(buf)
                        bytes_written += len(buf)
                        if image_size:
                            remote_cache.set("{}_uploading_size".format(image_id), bytes_written, 86400)

                if need_extend:
                    size_gb += 1
                    LOG.debug("Extending volume %(volume_id)s to %(size)s GB.",
                              {'volume_id': volume.id, 'size': size_gb})
                    volume.extend(volume, size_gb)
                    try:
                        volume = self._wait_volume_status(volume,
                                                          'extending',
                                                          'available')
                        size_gb = volume.size
                    except exceptions.BackendException:
                        raise exceptions.StorageFull()

            failed = False
        except IOError as e:
            # Convert IOError reasons to Glance Store exceptions
            errors = {errno.EFBIG: exceptions.StorageFull(),
                      errno.ENOSPC: exceptions.StorageFull(),
                      errno.EACCES: exceptions.StorageWriteDenied()}
            raise errors.get(e.errno, e)
        finally:
            if failed:
                LOG.error(_LE("Failed to write to volume %(volume_id)s."),
                          {'volume_id': volume.id})
                try:
                    volume.delete()
                except Exception:
                    LOG.exception(_LE('Failed to delete of volume '
                                      '%(volume_id)s.'),
                                  {'volume_id': volume.id})

        if image_size == 0:
            metadata.update({'image_size': str(bytes_written)})
            volume.update_all_metadata(metadata)
        volume.update_readonly_flag(volume, True)

        hash_hex = os_hash_value.hexdigest()
        checksum_hex = checksum.hexdigest()

        LOG.debug("Wrote %(bytes_written)d bytes to volume %(volume_id)s "
                  "with checksum %(checksum_hex)s.",
                  {'bytes_written': bytes_written,
                   'volume_id': volume.id,
                   'checksum_hex': checksum_hex})

        image_metadata = {}
        if self.backend_group:
            image_metadata['backend'] = u"%s" % self.backend_group
        if image_size == 0:
            image_size = bytes_written
        remote_cache.set("{}_uploading_size", image_size, 86400)

        return ('cinder://%s' % volume.id,
                bytes_written,
                checksum_hex,
                hash_hex,
                image_metadata)



```



修改/usr/lib/python2.7/site_packages/glance_store/_drivers/filesystem.py

```

    @glance_store.driver.back_compat_add
    @capabilities.check
    def add(self, image_id, image_file, image_size, hashing_algo, context=None,
            verifier=None):
        """
        Stores an image file with supplied identifier to the backend
        storage system and returns a tuple containing information
        about the stored image.

        :param image_id: The opaque image identifier
        :param image_file: The image data to write, as a file-like object
        :param image_size: The size of the image data to write, in bytes
        :param hashing_algo: A hashlib algorithm identifier (string)
        :param context: The request context
        :param verifier: An object used to verify signatures for images

        :returns: tuple of: (1) URL in backing store, (2) bytes written,
                  (3) checksum, (4) multihash value, and (5) a dictionary
                  with storage system specific information
        :raises: `glance_store.exceptions.Duplicate` if the image already
                 exists

        :note:: By default, the backend writes the image data to a file
              `/<DATADIR>/<ID>`, where <DATADIR> is the value of
              the filesystem_store_datadir configuration option and <ID>
              is the supplied image ID.
        """

        datadir = self._find_best_datadir(image_size)
        filepath = os.path.join(datadir, str(image_id))

        if os.path.exists(filepath):
            raise exceptions.Duplicate(image=filepath)
        os_hash_value = hashlib.new(str(hashing_algo))
        checksum = hashlib.md5()
        bytes_written = 0
        import memcache
        remote_cache = memcache.Client(["controller:11211"], debug=True)
        with open("/etc/glance/glance-api.conf", "r") as f:
            line_contents = f.readlines()
            for line_content in line_contents:
                if "memcached_servers =" in line_content and "NONE" not in line_content:
                    memcache_address = line_content.strip().split("=")[1].strip()
                    if memcache_address not in ["controller:11211"]:
                        remote_cache = memcache.Client([memcache_address], debug=True)
                    break
        if image_size:
            remote_cache.set("{}_total_size".format(image_id), image_size, 86400)
        else:
            remote_cache.set("{}_total_size".format(image_id), 1, 86400)
            remote_cache.set("{}_uploading_size", 0, 86400)

        try:
            with open(filepath, 'wb') as f:
                for buf in utils.chunkreadable(image_file,
                                               self.WRITE_CHUNKSIZE):
                    bytes_written += len(buf)
                    os_hash_value.update(buf)
                    checksum.update(buf)
                    if verifier:
                        verifier.update(buf)
                    f.write(buf)

                    if image_size:
                        remote_cache.set("{}_uploading_size".format(image_id), bytes_written, 86400)
        except IOError as e:
            if e.errno != errno.EACCES:
                self._delete_partial(filepath, image_id)
            errors = {errno.EFBIG: exceptions.StorageFull(),
                      errno.ENOSPC: exceptions.StorageFull(),
                      errno.EACCES: exceptions.StorageWriteDenied()}
            raise errors.get(e.errno, e)
        except Exception:
            with excutils.save_and_reraise_exception():
                self._delete_partial(filepath, image_id)

        hash_hex = os_hash_value.hexdigest()
        checksum_hex = checksum.hexdigest()
        metadata = self._get_metadata(filepath)

        LOG.debug(("Wrote %(bytes_written)d bytes to %(filepath)s with "
                   "checksum %(checksum_hex)s and multihash %(hash_hex)s"),
                  {'bytes_written': bytes_written,
                   'filepath': filepath,
                   'checksum_hex': checksum_hex,
                   'hash_hex': hash_hex})

        if self.backend_group:
            fstore_perm = getattr(
                self.conf, self.backend_group).filesystem_store_file_perm
        else:
            fstore_perm = self.conf.glance_store.filesystem_store_file_perm

        if fstore_perm > 0:
            perm = int(str(fstore_perm), 8)
            try:
                os.chmod(filepath, perm)
            except (IOError, OSError):
                LOG.warning(_LW("Unable to set permission to image: %s") %
                            filepath)

        # Add store backend information to location metadata
        if self.backend_group:
            metadata['backend'] = u"%s" % self.backend_group

        return ('file://%s' % filepath,
                bytes_written,
                checksum_hex,
                hash_hex,
                metadata)


```



